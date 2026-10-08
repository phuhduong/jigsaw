"""Model boundary contracts with a local structured-response fake."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fakes import drain
from llm import Budget, BudgetExceeded, ModelError, ModelGateway
from models import DesignRun, Usage
from pydantic import BaseModel


class Answer(BaseModel):
    value: int


class LocalModel:
    def __init__(self, responses=None):
        self.calls = 0
        self.messages = []
        self.responses = iter(responses or [{"value": "7"}])

    def with_structured_output(self, *args, **kwargs):
        return self

    def invoke(self, *args, **kwargs):
        self.calls += 1
        self.messages.append(list(args[0]))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return {
            "parsed": response,
            "raw": SimpleNamespace(usage_metadata={"input_tokens": 23, "output_tokens": 8}),
        }


class ModelGatewayTests(unittest.TestCase):
    def setUp(self):
        self.model = LocalModel()
        self.gateway = ModelGateway(self.model)
        self.gateway.rpm, self.gateway.tpm = 1000, 1000000
        self.run = DesignRun(
            original_request="Local fixture", usage=Usage(model_calls=2, input_tokens=10, output_tokens=5)
        )

    def test_model_allowances_must_be_positive(self):
        for setting in ("MODEL_RPM", "MODEL_TPM", "MODEL_CONTEXT_TOKENS"):
            with self.subTest(setting=setting), patch.dict("os.environ", {setting: "0"}):
                with self.assertRaisesRegex(ValueError, "must be positive integers"):
                    ModelGateway(self.model)

    def test_lazy_model_is_reused_across_calls(self):
        self.gateway.model = None
        self.model = LocalModel(responses=[{"value": 1}, {"value": 2}])
        with patch("llm.get_llm", return_value=self.model) as factory:
            values = [
                drain(self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {})).value
                for _ in range(2)
            ]
        self.assertEqual(values, [1, 2])
        factory.assert_called_once_with()

    def test_structured_result_is_validated_and_actual_usage_is_added(self):
        result = drain(self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100))
        self.assertIsInstance(result, Answer)
        self.assertEqual(result.value, 7)
        self.assertEqual(self.model.calls, 1)
        self.assertEqual(
            (self.run.usage.model_calls, self.run.usage.input_tokens, self.run.usage.output_tokens), (3, 33, 13)
        )

    def test_malformed_response_recovers_with_one_local_retry(self):
        self.gateway.model = LocalModel(responses=[None, {"value": "7"}])
        result = drain(self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100))
        self.assertEqual(result.value, 7)
        self.assertEqual(self.gateway.model.calls, 2)
        self.assertEqual(self.run.usage.model_calls, 4)

    def test_timeout_gets_one_retry_but_quota_does_not(self):
        for responses, expected_calls in (
            ([TimeoutError("The read operation timed out"), {"value": 7}], 2),
            ([TimeoutError("timed out"), TimeoutError("timed out")], 2),
            ([RuntimeError("429 RESOURCE_EXHAUSTED")], 1),
            ([TimeoutError("timed out"), RuntimeError("429 RESOURCE_EXHAUSTED")], 2),
        ):
            with self.subTest(responses=responses):
                self.gateway.model = LocalModel(responses)
                operation = self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100)
                if isinstance(responses[-1], dict):
                    self.assertEqual(drain(operation).value, 7)
                else:
                    with self.assertRaises(ModelError) as caught:
                        drain(operation)
                    if "429" in str(responses[-1]):
                        self.assertIn("Model quota exhausted", str(caught.exception))
                self.assertEqual(self.gateway.model.calls, expected_calls)

    def test_token_reservation_failure_does_not_consume_other_budgets(self):
        for field in ("input_tokens", "output_tokens"):
            with self.subTest(field=field):
                run = self.run.model_copy(deep=True)
                setattr(run.limits, field, getattr(run.usage, field) + 1)
                before = run.usage.model_dump(exclude={"elapsed_seconds"})
                with self.assertRaisesRegex(BudgetExceeded, field):
                    list(self.gateway.call(Budget(run), "fixture", Answer, "Return a value", {}, max_output=2))
                self.assertEqual(self.model.calls, 0)
                self.assertEqual(run.usage.model_dump(exclude={"elapsed_seconds"}), before)

    def test_invalid_field_gets_one_actionable_retry_without_echoing_input(self):
        self.gateway.model = LocalModel(responses=[{"value": "private-invalid-value"}, {"value": 7}])
        result = drain(self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100))
        self.assertEqual(result.value, 7)
        feedback = self.gateway.model.messages[-1][-1].content
        self.assertIn("value: Input should be a valid integer", feedback)
        self.assertNotIn("private-invalid-value", feedback)
        self.assertEqual(self.gateway.model.calls, 2)

    def test_repeated_invalid_fields_stop_with_a_useful_error(self):
        self.gateway.model = LocalModel(responses=[{}, {}])
        with self.assertRaisesRegex(ModelError, "value: Field required"):
            drain(self.gateway.call(Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100))
        self.assertEqual(self.gateway.model.calls, 2)


if __name__ == "__main__":
    unittest.main()
