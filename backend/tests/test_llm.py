"""Model boundary contracts with a local structured-response fake."""
from types import SimpleNamespace
import unittest

from pydantic import BaseModel

from llm import Budget, BudgetExceeded, ModelGateway
from models import DesignRun, Usage


class Answer(BaseModel):
    value: int


class LocalModel:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, *args, **kwargs):
        return self

    def invoke(self, *args, **kwargs):
        self.calls += 1
        return {"parsed": {"value": "7"},
                "raw": SimpleNamespace(usage_metadata={"input_tokens": 23, "output_tokens": 8})}


class ModelGatewayTests(unittest.TestCase):
    def setUp(self):
        self.model = LocalModel()
        self.gateway = ModelGateway(self.model)
        self.gateway.rpm, self.gateway.tpm = 1000, 1000000
        self.run = DesignRun(original_request="Local fixture",
                             usage=Usage(model_calls=2, input_tokens=10, output_tokens=5))

    def test_structured_result_is_validated_and_actual_usage_is_added(self):
        returned = []

        def invoke():
            returned.append((yield from self.gateway.call(
                Budget(self.run), "fixture", Answer, "Return a value", {}, max_output=100)))

        list(invoke())
        self.assertIsInstance(returned[0], Answer)
        self.assertEqual(returned[0].value, 7)
        self.assertEqual(self.model.calls, 1)
        self.assertEqual((self.run.usage.model_calls, self.run.usage.input_tokens,
                          self.run.usage.output_tokens), (3, 33, 13))

    def test_output_reservation_failure_does_not_consume_other_budgets(self):
        self.run.limits.output_tokens = 6
        before = self.run.usage.model_dump(exclude={"elapsed_seconds"})
        with self.assertRaises(BudgetExceeded):
            list(self.gateway.call(Budget(self.run), "fixture", Answer,
                                   "Return a value", {}, max_output=2))
        self.assertEqual(self.model.calls, 0)
        self.assertEqual(self.run.usage.model_dump(exclude={"elapsed_seconds"}), before)


if __name__ == "__main__":
    unittest.main()
