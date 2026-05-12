import socket
import subprocess
import sys
import time

import httpx
import pytest


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_server_is_ready(base_url: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/", timeout=0.5)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)

    raise TimeoutError("Server did not become ready in time")


@pytest.mark.integration
def test_root_endpoint_with_real_server() -> None:
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_until_server_is_ready(base_url)

        response = httpx.get(f"{base_url}/", timeout=2.0)

        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
    finally:
        process.terminate()
        process.wait(timeout=5)
