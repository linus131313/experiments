"""Tests for mcp-tool-latency-bench (pytest or plain python)."""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from server import make_server, process_request
from bench import _rpc, wait_for_port


# ── unit tests ────────────────────────────────────────────────────────────────

def test_process_request_returns_pong():
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "ping", "arguments": {}}}
    resp = process_request(msg)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["content"][0]["text"] == "pong"


def test_process_request_preserves_id():
    for id_val in [0, 42, "abc", None]:
        resp = process_request({"id": id_val})
        assert resp["id"] == id_val


def test_rpc_helper_is_valid_json():
    raw = _rpc(7).decode().strip()
    msg = json.loads(raw)
    assert msg["id"] == 7
    assert msg["jsonrpc"] == "2.0"


# ── integration helpers ───────────────────────────────────────────────────────

def _start_threaded_server(transport: str, port: int):
    """Start an HTTP/SSE server in a daemon thread; return the HTTPServer."""
    server = make_server(transport, port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    assert wait_for_port(port, timeout=3.0), f"Server on :{port} did not start"
    return server


# ── integration tests ─────────────────────────────────────────────────────────

def test_stdio_roundtrip():
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "server.py"), "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    try:
        proc.stdin.write(_rpc(1))
        proc.stdin.flush()
        line = proc.stdout.readline()
        resp = json.loads(line)
        assert resp["result"]["content"][0]["text"] == "pong"
        assert resp["id"] == 1
    finally:
        proc.terminate()
        proc.wait()


def test_http_roundtrip():
    server = _start_threaded_server("http", 18780)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:18780/messages",
            data=_rpc(2),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        assert data["result"]["content"][0]["text"] == "pong"
        assert data["id"] == 2
    finally:
        server.shutdown()


def test_sse_roundtrip():
    server = _start_threaded_server("sse", 18781)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:18781/messages",
            data=_rpc(3),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode()
        # SSE format: "data: <json>\n\n"
        assert raw.startswith("data: "), f"unexpected SSE body: {raw!r}"
        payload = json.loads(raw[len("data: "):].strip())
        assert payload["result"]["content"][0]["text"] == "pong"
        assert payload["id"] == 3
    finally:
        server.shutdown()


# ── standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback

    tests = [
        test_process_request_returns_pong,
        test_process_request_preserves_id,
        test_rpc_helper_is_valid_json,
        test_stdio_roundtrip,
        test_http_roundtrip,
        test_sse_roundtrip,
    ]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
