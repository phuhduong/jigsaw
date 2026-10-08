"""Narrow DigiKey MCP client. Supplier failures never become component records."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import requests
from urllib3.util import Timeout


class SupplierError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retry_after: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


def _parse_rpc_result(response: requests.Response, request_id: int) -> dict:
    """Read either MCP's JSON envelope or its complete SSE response."""
    try:
        # MCP JSON and SSE are UTF-8, even when requests defaults text/* to Latin-1.
        body = response.content.decode("utf-8").strip()
        if body.startswith("{"):
            messages = [json.loads(body)]
        else:
            messages = []
            for event in body.replace("\r\n", "\n").split("\n\n"):
                data = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
                if data:
                    messages.append(json.loads(data))
        for message in messages:
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise SupplierError(f"MCP request failed: {message['error'].get('message', 'unknown error')}")
            if isinstance(message.get("result"), dict):
                return message["result"]
    except (ValueError, TypeError, AttributeError) as exc:
        raise SupplierError("Invalid MCP response") from exc
    raise SupplierError("MCP response omitted the requested result")


class SupplierClient:
    def __init__(self, base_url: str | None = None, *, http: requests.Session | None = None):
        self.base_url = (base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8080")).rstrip("/")
        self.http = http or requests.Session()
        self.session_id: str | None = None
        self._request_id = 0

    def _post(self, payload: dict, deadline: float) -> requests.Response:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SupplierError("Supplier operation deadline exceeded")
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        try:
            response = self.http.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers=headers,
                timeout=Timeout(total=remaining),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            self.session_id = None
            status = exc.response.status_code if exc.response is not None else None
            raise SupplierError(
                f"Supplier transport failed (HTTP {status})"
                if status
                else "Supplier transport unavailable or timed out",
                status_code=status,
            ) from exc
        if time.monotonic() >= deadline:
            raise SupplierError("Supplier operation deadline exceeded")
        return response

    def _initialize(self, deadline: float) -> None:
        if self.session_id:
            return
        self._request_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "jigsaw-backend", "version": "0.2.0"},
                },
            },
            deadline,
        )
        _parse_rpc_result(response, self._request_id)
        self.session_id = response.headers.get("mcp-session-id")
        if not self.session_id:
            raise SupplierError("MCP initialization omitted its session ID")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, deadline)

    def _call(self, name: str, arguments: dict, timeout: float) -> Any:
        if timeout <= 0:
            raise SupplierError("Supplier operation deadline exceeded")
        deadline = time.monotonic() + timeout
        # Carries the same budget through MCP to OAuth and DigiKey.
        deadline_ms = (time.time() + timeout) * 1000
        self._initialize(deadline)
        for attempt in range(2):
            self._request_id += 1
            try:
                response = self._post(
                    {
                        "jsonrpc": "2.0",
                        "id": self._request_id,
                        "method": "tools/call",
                        "params": {"name": name, "arguments": {**arguments, "deadline_ms": deadline_ms}},
                    },
                    deadline,
                )
                break
            except SupplierError as error:
                if attempt or error.status_code != 404:
                    raise
                # The MCP server expires idle sessions; reconnect within this operation's deadline.
                self._initialize(deadline)
        result = _parse_rpc_result(response, self._request_id)
        try:
            content = next(item["text"] for item in result.get("content", []) if item.get("type") == "text")
            data = json.loads(content)
        except (StopIteration, KeyError, TypeError, ValueError) as exc:
            raise SupplierError("MCP tool returned no valid supplier data") from exc
        if result.get("isError"):
            detail = data.get("error", {}) if isinstance(data, dict) else {}
            raise SupplierError(
                detail.get("message", "Supplier lookup failed"),
                status_code=detail.get("status_code"),
                retry_after=detail.get("retry_after"),
            )
        return data

    def search(
        self, query: str, *, region: str = "US", currency: str = "USD", timeout: float = 20, limit: int = 3
    ) -> list[dict]:
        products = self._call(
            "search_components",
            {"query": query, "region": region, "currency": currency, "limit": limit},
            timeout,
        )
        if not isinstance(products, list) or any(not isinstance(product, dict) for product in products):
            raise SupplierError("Supplier search returned an invalid product list")
        return products

    def get_product(self, mpn: str, *, region: str = "US", currency: str = "USD", timeout: float = 20) -> dict:
        """The identifier may also be a DigiKey SKU, avoiding ambiguous manufacturer MPNs."""
        product = self._call("get_product", {"mpn": mpn, "region": region, "currency": currency}, timeout)
        if not isinstance(product, dict) or not product.get("mpn") or not product.get("manufacturer"):
            raise SupplierError("Supplier details returned no exact product identity")
        return product
