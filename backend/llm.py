"""Model portability, resource accounting and bounded calls; no orchestration framework."""

from __future__ import annotations

import json
import logging
import os
import time
from collections import deque

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from models import DesignRun
from pydantic import BaseModel, ValidationError


class BudgetExceeded(RuntimeError):
    pass


class ModelError(RuntimeError):
    pass


def _describe_schema_error(error):
    """Expose schema fields/rules, never the provider's raw response or input values."""
    while error.__cause__ is not None:
        error = error.__cause__
    if isinstance(error, ValidationError):
        return "; ".join(
            f"{'.'.join(map(str, item['loc'])) or 'response'}: {item['msg']}"
            for item in error.errors(include_input=False, include_context=False, include_url=False)
        )[:500]
    return type(error).__name__


class Budget:
    def __init__(self, run: DesignRun):
        self.run = run
        self.started = time.monotonic()

    def remaining(self) -> float:
        self.run.usage.elapsed_seconds = round(time.monotonic() - self.started, 2)
        left = self.run.limits.seconds - self.run.usage.elapsed_seconds
        if left <= 0:
            raise BudgetExceeded("Run time budget exhausted")
        return left

    def consume(self, field: str, amount: int = 1):
        self.remaining()
        used = getattr(self.run.usage, field)
        if used + amount > getattr(self.run.limits, field):
            raise BudgetExceeded(f"Run {field} budget exhausted")
        setattr(self.run.usage, field, used + amount)


def get_llm():
    provider = os.getenv("MODEL_PROVIDER", "google_genai")
    options = {"max_retries": 0, "timeout": 45}
    if provider == "google_genai":
        if not os.getenv("GEMINI_API_KEY"):
            raise ModelError("GEMINI_API_KEY is not configured")
        options["api_key"] = os.environ["GEMINI_API_KEY"]
        if os.getenv("MODEL_THINKING_LEVEL"):
            options["thinking_level"] = os.environ["MODEL_THINKING_LEVEL"]
    return init_chat_model(
        os.getenv("MODEL", "gemini-3.5-flash-lite"),
        model_provider=provider,
        **options,
    )


# The server admits one run at a time. Keep the rolling window across consecutive runs.
_requests: deque[tuple[float, int]] = deque()


class ModelGateway:
    def __init__(self, model=None):
        self.model = model
        self.pdf_supported = os.getenv("MODEL_PDF_INPUT", "true").lower() == "true"
        self.rpm = int(os.getenv("MODEL_RPM", "15"))
        self.tpm = int(os.getenv("MODEL_TPM", "250000"))
        self.context_limit = int(os.getenv("MODEL_CONTEXT_TOKENS", "1048576"))

    def call(self, budget, stage, schema, instructions, payload, blocks=None, *, max_output=3000, pdf_pages=0):
        """Yield progress before each attempt; return validated data through yield-from."""
        if pdf_pages and not self.pdf_supported:
            raise ModelError("Configured model has no verified PDF input capability")
        payload_text = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=lambda value: value.model_dump(mode="json") if isinstance(value, BaseModel) else str(value),
        )
        blocks = blocks or []
        # PDF bytes are not text tokens. Reserve separately for page input.
        text_size = len(instructions) + len(payload_text) + len(json.dumps(schema.model_json_schema()))
        text_size += sum(len(block.get("text", "")) for block in blocks)
        estimate = (text_size + 2) // 3 + pdf_pages * 1200
        if estimate + max_output > self.context_limit or estimate > self.tpm:
            raise BudgetExceeded("Required source context exceeds the configured model allowance")
        messages = [
            SystemMessage(content=instructions),
            HumanMessage(content=[{"type": "text", "text": payload_text}, *blocks]),
        ]
        model = self.model or get_llm()
        for attempt in range(2):
            budget.remaining()
            while True:
                current = time.monotonic()
                while _requests and current - _requests[0][0] >= 60:
                    _requests.popleft()
                if len(_requests) < self.rpm and sum(tokens for _, tokens in _requests) + estimate <= self.tpm:
                    break
                wait = max(0, 60.1 - (current - _requests[0][0]))
                if wait > budget.remaining():
                    raise BudgetExceeded("Model rate limit exceeds the remaining run time; retry later")
                pause = min(50, wait)
                yield {"type": "progress", "stage": stage, "message": f"Waiting {pause:.0f}s for model quota"}
                time.sleep(pause)
            reservation = {
                "model_calls": 1,
                "input_tokens": estimate,
                "output_tokens": max_output,
                "pdf_pages": pdf_pages,
            }
            for field, amount in reservation.items():
                if getattr(budget.run.usage, field) + amount > getattr(budget.run.limits, field):
                    raise BudgetExceeded(f"Run {field} budget exhausted")
            for field, amount in reservation.items():
                budget.consume(field, amount)
            _requests.append((time.monotonic(), estimate))
            yield {"type": "progress", "stage": stage, "message": f"{stage}: model attempt {attempt + 1}"}
            try:
                result = model.with_structured_output(schema, method="json_schema", include_raw=True).invoke(
                    messages,
                    max_output_tokens=max_output,
                    timeout=min(45, budget.remaining()),
                    max_retries=0,
                )
                raw = result.get("raw")
                usage = getattr(raw, "usage_metadata", None)
                if usage:
                    logging.getLogger(__name__).info(
                        "%s: input=%s output=%s",
                        stage,
                        usage.get("input_tokens"),
                        usage.get("output_tokens"),
                    )
                    budget.run.usage.input_tokens += usage.get("input_tokens", estimate) - estimate
                    budget.run.usage.output_tokens += usage.get("output_tokens", max_output) - max_output
                    if (
                        budget.run.usage.input_tokens > budget.run.limits.input_tokens
                        or budget.run.usage.output_tokens > budget.run.limits.output_tokens
                    ):
                        raise BudgetExceeded("Reported model usage exhausted the run token budget")
                if result.get("parsing_error"):
                    raise ModelError("Model response rejected: " + _describe_schema_error(result["parsing_error"]))
                if result.get("parsed") is None:
                    raise ModelError("Model response did not match the required schema")
                parsed = result["parsed"]
                return parsed if isinstance(parsed, schema) else schema.model_validate(parsed)
            except BudgetExceeded:
                raise
            except Exception as error:
                message = _describe_schema_error(error) if isinstance(error, ValidationError) else str(error)
                for key in ("GEMINI_API_KEY", "LANGCHAIN_API_KEY", "LANGSMITH_API_KEY"):
                    secret = os.getenv(key)
                    if secret:
                        message = message.replace(secret, "[redacted]")
                quota_exhausted = "429" in message or "RESOURCE_EXHAUSTED" in message
                transient = quota_exhausted or any(
                    code in message for code in ("500", "502", "503", "504", "UNAVAILABLE")
                )
                malformed = isinstance(error, (ModelError, ValidationError))
                if not attempt and (transient or malformed):
                    if transient:
                        # Do not hammer a quota-exhausted provider or hide requests in SDK retries.
                        if quota_exhausted:
                            raise ModelError(
                                "Model quota exhausted; saved a partial result. Retry after quota resets"
                            ) from error
                        yield {
                            "type": "progress",
                            "stage": stage,
                            "message": "Provider temporarily unavailable; retrying once",
                        }
                        time.sleep(min(2, budget.remaining()))
                    else:
                        messages.append(
                            HumanMessage(
                                content=f"Schema rejection: {message[:500]}. Return a complete valid response matching the requested schema."
                            )
                        )
                    continue
                raise ModelError(message[:500]) from error
