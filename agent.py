import json
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


OLLAYA_URL = "http://127.0.0.1:11435/api/decide"
QUESTIONS = {
    "sentiment": {
        "type": "choice",
        "instructions": "What sentiment does this text express?",
        "criteria": {
            "Positive": "The text expresses positive sentiment", 
            "Negative": "The text expresses negative sentiment",
        },
    },
}


class AgentHandler(BaseHTTPRequestHandler):
    def respond(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error(self, status: int, message: str, code: str) -> None:
        self.log_error("%s: %s", code, message)
        self.respond(
            status,
            json.dumps({"error": message, "code": code}).encode("utf-8"),
        )

    def do_GET(self) -> None:
        if self.path != "/":
            self.error(404, "Only GET / is supported.", "NOT_FOUND")
            return
        if self.headers.get("Transfer-Encoding"):
            self.error(
                501, "Use Content-Length, not Transfer-Encoding.", "NOT_IMPLEMENTED"
            )
            return
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            self.error(
                411, "A UTF-8 body with Content-Length is required.", "LENGTH_REQUIRED"
            )
            return
        try:
            length = int(length_header)
        except ValueError:
            self.error(400, "Content-Length must be an integer.", "INVALID_REQUEST")
            return
        if length <= 0:
            self.error(400, "A nonempty UTF-8 body is required.", "INVALID_REQUEST")
            return
        body = self.rfile.read(length)
        if len(body) != length:
            self.error(400, "The request body is incomplete.", "INVALID_REQUEST")
            return
        try:
            state = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.error(400, str(exc), "INVALID_UTF8")
            return

        request = Request(
            OLLAYA_URL,
            data=json.dumps(
                {"model": "laya:latest", "state": state, "questions": QUESTIONS}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            # Keep local text out of any configured HTTP proxy.
            try:
                response = build_opener(ProxyHandler({})).open(request, timeout=60)
            except HTTPError as exc:
                self.log_error("Ollaya returned HTTP %s: %s", exc.code, exc.reason)
                response = exc
            with response:
                status = response.status
                result = response.read()
        except (URLError, OSError, HTTPException) as exc:
            self.error(
                502,
                f"Cannot communicate with Ollaya at {OLLAYA_URL}: "
                f"{type(exc).__name__}: {exc}",
                "OLLAYA_UNAVAILABLE",
            )
            return
        self.respond(status, result)


if __name__ == "__main__":
    with ThreadingHTTPServer(("0.0.0.0", 8080), AgentHandler) as server:
        print("Listening on 0.0.0.0:8080", flush=True)
        server.serve_forever()