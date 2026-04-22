"""Minimal JSON-RPC 2.0 server for MCP tool-call latency benchmark.

Supports three transports:
  stdio  – newline-delimited JSON on stdin/stdout
  http   – plain HTTP POST → JSON response
  sse    – HTTP POST → Server-Sent Events response (MCP SSE style)
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def process_request(msg: dict) -> dict:
    """Return a JSON-RPC 2.0 'pong' response for any incoming request."""
    return {
        "jsonrpc": "2.0",
        "id": msg.get("id"),
        "result": {"content": [{"type": "text", "text": "pong"}]},
    }


def run_stdio() -> None:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
            resp = process_request(msg)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "Parse error"}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


class _BaseHandler(BaseHTTPRequestHandler):
    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def log_message(self, *_args) -> None:
        pass  # suppress per-request logging


class HTTPHandler(_BaseHandler):
    def do_POST(self) -> None:
        resp = json.dumps(process_request(self._read_body())).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


class SSEHandler(_BaseHandler):
    def do_POST(self) -> None:
        data = json.dumps(process_request(self._read_body()))
        body = f"data: {data}\n\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_server(transport: str, port: int) -> HTTPServer:
    handler = HTTPHandler if transport == "http" else SSEHandler
    return HTTPServer(("127.0.0.1", port), handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latency-bench MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.transport == "stdio":
        run_stdio()
    else:
        make_server(args.transport, args.port).serve_forever()
