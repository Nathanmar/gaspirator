"""Contract testing with the Prism validation proxy (https://stoplight.io/open-source/prism).

The API is served by uvicorn on a free local port and Prism proxies it, validating every
request and response against openapi.yaml. Prism does not block anything (no `--errors`):
it reports the violations in the `sl-violations` header, checked by `assert_contract`.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

PRISM_VERSION = "5.15.10"  # keep in sync with the prism image of docker-compose.yml
SPEC_PATH = Path(__file__).resolve().parents[3] / "openapi.yaml"
# Prism matches the `paths` of the contract without the `servers` base path.
API_PREFIX = "/api/v1"
STARTUP_TIMEOUT = 180  # first run downloads Prism with npx


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(port: int, process: subprocess.Popen | None = None) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"Prism exited with code {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"Nothing listening on port {port} after {STARTUP_TIMEOUT}s")


def _stop(process: subprocess.Popen) -> None:
    """Stop npx and the Prism node process it spawned."""
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False
        )
    else:
        os.killpg(process.pid, signal.SIGTERM)
    process.wait(timeout=10)


@contextmanager
def serve_api(app: FastAPI) -> Iterator[str]:
    """Run the app with uvicorn in a background thread; yield its base URL."""
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        _wait_for_port(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


@contextmanager
def prism_proxy(upstream: str) -> Iterator[str]:
    """Run `prism proxy openapi.yaml <upstream>`; yield the proxy base URL."""
    npx = shutil.which("npx")
    if npx is None:
        raise RuntimeError("npx (Node.js) is required to run the Prism contract tests")
    port = _free_port()
    command = [
        npx, "--yes", f"@stoplight/prism-cli@{PRISM_VERSION}", "proxy", str(SPEC_PATH),
        upstream, "--host", "127.0.0.1", "--port", str(port),
    ]  # fmt: skip
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            try:
                _wait_for_port(port, process)
            except (RuntimeError, TimeoutError) as exc:
                log.seek(0)
                output = log.read().decode(errors="replace")
                raise RuntimeError(f"Prism did not start: {exc}\n{output}") from exc
            yield f"http://127.0.0.1:{port}"
        finally:
            _stop(process)


def violations(response) -> list[dict]:
    """Violations reported by Prism for this exchange (`sl-violations` header)."""
    return json.loads(response.headers.get("sl-violations", "[]"))


def assert_contract(response, *, invalid_request: bool = False) -> None:
    """Fail on contract violations reported by Prism.

    Any response violation fails (an undocumented status code is only a Warning for
    Prism), as do request violations of severity Error. `invalid_request=True` is for
    tests that break the contract on purpose (missing field, missing token...): only the
    response is then checked. Malformed JSON cannot go through Prism (it never answers):
    send it with the in-process `client` fixture instead.
    """
    errors = [
        violation
        for violation in violations(response)
        if violation.get("location", [""])[0] == "response"
        or (not invalid_request and violation.get("severity") == "Error")
    ]
    assert not errors, f"Contract violations reported by Prism: {errors}"
