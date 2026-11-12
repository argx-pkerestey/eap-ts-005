import io
import json
import threading
import unittest
from http.client import HTTPConnection, IncompleteRead
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from agent import AgentHandler, QUESTIONS


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, body, path="/", headers=None):
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request("GET", path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    @patch("agent.build_opener")
    def test_unicode_and_independent_questions_preserve_complete_response(self, opener):
        result = b'{"answers":{"positive":{"noul":0.8},"negative":{"noul":0.7}},"usage":{}}'
        response = MagicMock(status=200)
        response.read.return_value = result
        opener.return_value.open.return_value = response
        text = "Tr\u00e8s bien, but the service was terrible."

        self.assertEqual(self.request(text.encode("utf-8")), (200, result))
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            json.loads(request.data),
            {"model": "laya:latest", "state": text, "questions": QUESTIONS},
        )
        self.assertEqual(
            [question["type"] for question in json.loads(request.data)["questions"].values()],
            ["noul", "noul"],
        )

    @patch("agent.build_opener")
    def test_upstream_http_error_is_preserved(self, opener):
        body = b'{"error":"model missing","code":"MODEL_NOT_FOUND"}'
        opener.return_value.open.side_effect = HTTPError(
            "http://127.0.0.1:11435/api/decide", 404, "Not Found", {}, io.BytesIO(body)
        )
        self.assertEqual(self.request(b"text"), (404, body))

    @patch("agent.build_opener")
    def test_communication_failures_include_exception_details(self, opener):
        for error in (
            URLError("connection refused"),
            TimeoutError("timed out"),
            IncompleteRead(b"partial", 100),
        ):
            with self.subTest(error=type(error).__name__):
                opener.return_value.open.side_effect = error
                status, body = self.request(b"text")
                self.assertEqual(status, 502)
                result = json.loads(body)
                self.assertEqual(result["code"], "OLLAYA_UNAVAILABLE")
                self.assertIn(str(error), result["error"])
                self.assertIn(type(error).__name__, result["error"])

    @patch("agent.build_opener")
    def test_incomplete_upstream_body_returns_json_error(self, opener):
        response = MagicMock(status=200)
        response.read.side_effect = IncompleteRead(b"partial", 100)
        opener.return_value.open.return_value = response
        status, body = self.request(b"text")
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["code"], "OLLAYA_UNAVAILABLE")

    @patch("agent.build_opener")
    def test_invalid_requests_do_not_reach_ollaya(self, opener):
        cases = [
            (b"", "/", {}, 400),
            (b"\xff", "/", {}, 400),
            (b"text", "/missing", {}, 404),
            (None, "/", {}, 411),
            (b"text", "/", {"Content-Length": "invalid"}, 400),
            (b"", "/", {"Content-Length": "-1"}, 400),
            (b"text", "/", {"Transfer-Encoding": "chunked"}, 501),
        ]
        for body, path, headers, expected_status in cases:
            with self.subTest(path=path, headers=headers, body=body):
                status, result = self.request(body, path, headers)
                self.assertEqual(status, expected_status)
                self.assertIn("error", json.loads(result))
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
