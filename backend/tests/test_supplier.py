"""Supplier boundary tests use only a local fake MCP transport."""

import json as jsonlib
import unittest

import requests
from tools import SupplierClient, SupplierError


class FakeMCP:
    def __init__(self, fail=False):
        self.fail = fail
        self.lookups = []

    def post(self, url, *, json: dict, headers, timeout):
        payload = json
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "text/event-stream"
        response.encoding = requests.utils.get_encoding_from_headers(response.headers)
        if payload["method"] == "initialize":
            response.headers["mcp-session-id"] = "local-fake-session"
            body = {"jsonrpc": "2.0", "id": payload["id"], "result": {"protocolVersion": "2025-03-26"}}
        elif payload["method"] == "notifications/initialized":
            response.status_code = 202
            response._content = b""
            return response
        else:
            self.lookups.append(payload["params"])
            part = {
                "manufacturer": "Example",
                "mpn": "SENSOR-1",
                "offers": [],
                "parameters": [
                    {"name": "Tolerance", "value": "±1%"},
                    {"name": "Operating Temperature", "value": "-40°C"},
                ],
            }
            data = (
                {"error": {"message": "DigiKey request failed (HTTP 429)", "status_code": 429, "retry_after": "20"}}
                if self.fail
                else ([part] if payload["params"]["name"] == "search_components" else part)
            )
            body = {
                "jsonrpc": "2.0",
                "id": payload["id"],
                "result": {
                    "isError": self.fail,
                    "content": [{"type": "text", "text": jsonlib.dumps(data, ensure_ascii=False)}],
                },
            }
        response._content = ("event: message\ndata: " + jsonlib.dumps(body, ensure_ascii=False) + "\n\n").encode(
            "utf-8"
        )
        return response


class SupplierTests(unittest.TestCase):
    def test_search_and_details_preserve_products_and_locale(self):
        fake = FakeMCP()
        client = SupplierClient(http=fake)
        product = client.search("sensor", region="CA", currency="CAD")[0]
        self.assertEqual(product["mpn"], "SENSOR-1")
        self.assertEqual([p["value"] for p in product["parameters"]], ["±1%", "-40°C"])
        self.assertEqual(client.get_product("SENSOR-1")["manufacturer"], "Example")
        self.assertEqual(fake.lookups[0]["arguments"]["currency"], "CAD")
        self.assertEqual(fake.lookups[0]["arguments"]["limit"], 3)

    def test_tool_error_is_a_typed_error_without_retry(self):
        fake = FakeMCP(fail=True)
        with self.assertRaises(SupplierError) as caught:
            SupplierClient(http=fake).search("sensor")
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(caught.exception.retry_after, "20")
        self.assertEqual(len(fake.lookups), 1)

    def test_expired_session_reconnects_without_extending_the_lookup_deadline(self):
        class ExpiredSession(FakeMCP):
            def __init__(self):
                super().__init__()
                self.deadlines = []

            def post(self, url, *, json, headers, timeout):
                if json["method"] == "tools/call":
                    self.deadlines.append(json["params"]["arguments"]["deadline_ms"])
                    if headers.get("mcp-session-id") == "expired":
                        response = requests.Response()
                        response.status_code = 404
                        response._content = b"Session not found"
                        return response
                return super().post(url, json=json, headers=headers, timeout=timeout)

        fake = ExpiredSession()
        client = SupplierClient(http=fake)
        client.session_id = "expired"
        self.assertEqual(client.search("sensor")[0]["mpn"], "SENSOR-1")
        self.assertEqual(client.session_id, "local-fake-session")
        self.assertEqual(len(fake.deadlines), 2)
        self.assertEqual(fake.deadlines[0], fake.deadlines[1])


if __name__ == "__main__":
    unittest.main()
