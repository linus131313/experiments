"""Benchmark MCP tool-call round-trip latency across stdio, HTTP, and SSE transports.

Usage:
    python bench.py                  # all three transports, 100 iterations each
    python bench.py --n 50           # fewer iterations
    python bench.py --transport sse  # single transport
"""

import argparse
import json
import os
import socket
import statistics
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "server.py")

N_WARMUP = 10
N_BENCH_DEFAULT = 100


def _rpc(n: int) -> bytes:
    return (
        json.dumps({
            "jsonrpc": "2.0", "id": n,
            "method": "tools/call",
            "params": {"name": "ping", "arguments": {}},
        }) + "\n"
    ).encode()


def wait_for_port(port: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def bench_stdio(n: int = N_BENCH_DEFAULT) -> list[float]:
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    latencies: list[float] = []
    try:
        for i in range(n + N_WARMUP):
            t0 = time.perf_counter()
            proc.stdin.write(_rpc(i))
            proc.stdin.flush()
            proc.stdout.readline()
            dt = (time.perf_counter() - t0) * 1000
            if i >= N_WARMUP:
                latencies.append(dt)
    finally:
        proc.terminate()
        proc.wait()
    return latencies


def _http_post(url: str, body: bytes) -> None:
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


def bench_http_like(transport: str, port: int, n: int = N_BENCH_DEFAULT) -> list[float]:
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--transport", transport, "--port", str(port)]
    )
    try:
        if not wait_for_port(port):
            raise RuntimeError(f"Server on :{port} did not start within 5 s")
        url = f"http://127.0.0.1:{port}/messages"
        latencies: list[float] = []
        for i in range(n + N_WARMUP):
            t0 = time.perf_counter()
            _http_post(url, _rpc(i))
            dt = (time.perf_counter() - t0) * 1000
            if i >= N_WARMUP:
                latencies.append(dt)
    finally:
        proc.terminate()
        proc.wait()
    return latencies


def print_stats(name: str, latencies: list[float]) -> None:
    s = sorted(latencies)
    n = len(s)
    print(f"\n{'─' * 42}")
    print(f"  Transport : {name}")
    print(f"  n         : {n}")
    print(f"  mean      : {statistics.mean(s):.3f} ms")
    print(f"  median    : {statistics.median(s):.3f} ms")
    print(f"  stdev     : {statistics.stdev(s):.3f} ms")
    print(f"  p95       : {s[int(0.95 * n)]:.3f} ms")
    print(f"  p99       : {s[min(int(0.99 * n), n - 1)]:.3f} ms")
    print(f"  min / max : {s[0]:.3f} / {s[-1]:.3f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP tool-call latency benchmark")
    parser.add_argument("--n", type=int, default=N_BENCH_DEFAULT,
                        help="iterations per transport (default: 100)")
    parser.add_argument("--transport", choices=["stdio", "http", "sse", "all"],
                        default="all")
    args = parser.parse_args()

    transports = ["stdio", "http", "sse"] if args.transport == "all" else [args.transport]
    results: dict[str, list[float]] = {}

    print("MCP Tool-Call Latency Benchmark")
    print("================================")

    if "stdio" in transports:
        print(f"\n[stdio] warming up ({N_WARMUP}) then measuring ({args.n}) …")
        results["stdio"] = bench_stdio(args.n)
        print_stats("stdio", results["stdio"])

    if "http" in transports:
        print(f"\n[http]  warming up ({N_WARMUP}) then measuring ({args.n}) …")
        results["http"] = bench_http_like("http", 18765, args.n)
        print_stats("http", results["http"])

    if "sse" in transports:
        print(f"\n[sse]   warming up ({N_WARMUP}) then measuring ({args.n}) …")
        results["sse"] = bench_http_like("sse", 18766, args.n)
        print_stats("sse", results["sse"])

    if len(results) > 1:
        print(f"\n{'─' * 42}")
        print("Summary (median latency, ms):")
        for name, lats in results.items():
            print(f"  {name:<6}: {statistics.median(lats):.3f}")


if __name__ == "__main__":
    main()
