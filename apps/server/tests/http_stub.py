"""A local HTTP server standing in for an external API (Géoplateforme, Recherche
d'entreprises) in the tests of their clients: no request leaves the tests."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit


class StubApi:
    """What the stub answers to every GET, and the requests it received."""

    def __init__(self) -> None:
        self.status = 200
        self.body: bytes = b"{}"
        self.requests: list[tuple[str, dict[str, list[str]], dict[str, str]]] = []

    def answer_json(self, data) -> None:
        self.body = json.dumps(data).encode()

    @property
    def last_request(self) -> tuple[str, dict[str, list[str]], dict[str, str]]:
        """(path, query parameters, headers) of the last request."""
        return self.requests[-1]


@contextmanager
def stub_api() -> Iterator[tuple[StubApi, str]]:
    """Serve a `StubApi` on a free local port; yield it and its base URL."""
    state = StubApi()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            url = urlsplit(self.path)
            state.requests.append((url.path, parse_qs(url.query), dict(self.headers)))
            self.send_response(state.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(state.body)

        def log_message(self, *args) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
