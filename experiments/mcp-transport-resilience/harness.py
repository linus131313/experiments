"""
mcp-transport-resilience: fault-injection harness for MCP-style JSON-RPC transport.

Simulates drop, reorder, and duplicate faults on asyncio queues that model
an MCP stdio channel, then measures how a retrying client recovers.

Usage:
    python harness.py                      # run default scenario grid
    python harness.py --drop 0.3           # single run with 30% drop rate
"""
import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Config and statistics
# ---------------------------------------------------------------------------

@dataclass
class FaultConfig:
    drop_rate: float = 0.0       # fraction of messages silently dropped
    reorder_rate: float = 0.0    # fraction of messages delayed (simulates reorder)
    duplicate_rate: float = 0.0  # fraction of messages sent twice
    reorder_delay_s: float = 0.08
    seed: Optional[int] = 42


@dataclass
class RunStats:
    requests: int = 0
    successes: int = 0
    retries: int = 0
    timeouts: int = 0
    latencies: list = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.successes / self.requests if self.requests else 0.0

    @property
    def mean_latency_ms(self) -> float:
        return 1000 * sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def summary(self) -> dict:
        return {
            "requests": self.requests,
            "successes": self.successes,
            "success_rate": round(self.success_rate, 3),
            "retries": self.retries,
            "timeouts": self.timeouts,
            "mean_latency_ms": round(self.mean_latency_ms, 2),
        }


# ---------------------------------------------------------------------------
# Mock MCP server (in-process, responds to JSON-RPC over asyncio queues)
# ---------------------------------------------------------------------------

class MockMCPServer:
    """Minimal JSON-RPC server supporting initialize and tools/call."""

    TOOLS = {
        "echo": lambda args: {"echoed": args.get("text", "")},
        "add": lambda args: {"result": args.get("a", 0) + args.get("b", 0)},
    }

    def __init__(self, inbox: asyncio.Queue, outbox: asyncio.Queue):
        self.inbox = inbox
        self.outbox = outbox

    async def run(self):
        while True:
            msg = await self.inbox.get()
            if msg is None:
                break
            await self.outbox.put(self._handle(msg))

    def _handle(self, msg: dict) -> dict:
        method = msg.get("method", "")
        rid = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mock", "version": "0.1"},
            }}

        if method == "tools/call":
            name = params.get("name", "")
            if name in self.TOOLS:
                result = self.TOOLS[name](params.get("arguments", {}))
                return {"jsonrpc": "2.0", "id": rid, "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                }}
            return {"jsonrpc": "2.0", "id": rid, "error": {
                "code": -32601, "message": f"unknown tool: {name}",
            }}

        return {"jsonrpc": "2.0", "id": rid, "error": {
            "code": -32601, "message": f"unknown method: {method}",
        }}


# ---------------------------------------------------------------------------
# Fault-injecting proxy
# ---------------------------------------------------------------------------

class FaultProxy:
    """
    Sits between client and server queues. Injects faults based on FaultConfig.
    Each _relay task forwards one direction; faults only apply on the request path.
    """

    def __init__(self, config: FaultConfig):
        self.cfg = config
        self.rng = random.Random(config.seed)
        # queues from client's perspective
        self.client_out: asyncio.Queue = asyncio.Queue()
        self.client_in: asyncio.Queue = asyncio.Queue()
        # queues from server's perspective
        self.server_out: asyncio.Queue = asyncio.Queue()
        self.server_in: asyncio.Queue = asyncio.Queue()

    async def start(self):
        asyncio.create_task(self._relay_with_faults(self.client_out, self.server_in))
        asyncio.create_task(self._relay_clean(self.server_out, self.client_in))

    async def _relay_with_faults(self, src: asyncio.Queue, dst: asyncio.Queue):
        while True:
            msg = await src.get()
            if msg is None:
                await dst.put(None)
                return

            r = self.rng.random()
            if r < self.cfg.drop_rate:
                continue  # silently drop

            r2 = self.rng.random()
            if r2 < self.cfg.duplicate_rate:
                await dst.put(msg)
                await dst.put(msg)
                continue

            r3 = self.rng.random()
            if r3 < self.cfg.reorder_rate:
                delay = self.cfg.reorder_delay_s
                loop = asyncio.get_event_loop()
                loop.call_later(delay, lambda m=msg: loop.call_soon_threadsafe(dst.put_nowait, m))
                continue

            await dst.put(msg)

    async def _relay_clean(self, src: asyncio.Queue, dst: asyncio.Queue):
        while True:
            msg = await src.get()
            await dst.put(msg)
            if msg is None:
                return


# ---------------------------------------------------------------------------
# Retrying client
# ---------------------------------------------------------------------------

class MCPClient:
    """
    Sends JSON-RPC requests and retries on timeout. Tracks RunStats.
    """

    def __init__(self, outbox: asyncio.Queue, inbox: asyncio.Queue,
                 timeout_s: float = 0.15, max_retries: int = 3):
        self.outbox = outbox
        self.inbox = inbox
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self._next_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self.stats = RunStats()

    async def start(self):
        asyncio.create_task(self._dispatch_responses())

    async def _dispatch_responses(self):
        while True:
            resp = await self.inbox.get()
            if resp is None:
                break
            rid = resp.get("id")
            if rid in self._pending and not self._pending[rid].done():
                self._pending[rid].set_result(resp)

    async def call(self, method: str, params: dict) -> Optional[dict]:
        """Send a request, retry up to max_retries times on timeout."""
        self.stats.requests += 1
        t0 = time.perf_counter()

        for attempt in range(self.max_retries + 1):
            rid = self._next_id
            self._next_id += 1
            fut: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending[rid] = fut

            msg = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params}
            await self.outbox.put(msg)

            try:
                resp = await asyncio.wait_for(asyncio.shield(fut), timeout=self.timeout_s)
                self.stats.successes += 1
                self.stats.latencies.append(time.perf_counter() - t0)
                return resp
            except asyncio.TimeoutError:
                self.stats.timeouts += 1
                if attempt < self.max_retries:
                    self.stats.retries += 1
                else:
                    return None
            finally:
                self._pending.pop(rid, None)

        return None


# ---------------------------------------------------------------------------
# Harness runner
# ---------------------------------------------------------------------------

async def run_scenario(config: FaultConfig, n_requests: int = 40) -> RunStats:
    proxy = FaultProxy(config)
    server = MockMCPServer(proxy.server_in, proxy.server_out)

    await proxy.start()
    asyncio.create_task(server.run())

    client = MCPClient(proxy.client_out, proxy.client_in, timeout_s=0.15, max_retries=3)
    await client.start()

    # initialize handshake
    await client.call("initialize", {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "test-client", "version": "0.1"},
    })

    # workload: alternate between two tools
    calls = [
        ("tools/call", {"name": "echo", "arguments": {"text": f"msg-{i}"}})
        for i in range(n_requests // 2)
    ] + [
        ("tools/call", {"name": "add", "arguments": {"a": i, "b": i * 2}})
        for i in range(n_requests // 2)
    ]
    random.Random(config.seed).shuffle(calls)

    for method, params in calls:
        await client.call(method, params)

    await proxy.client_out.put(None)
    return client.stats


def print_table(results: list[tuple[FaultConfig, RunStats]]):
    header = f"{'drop':>5} {'reord':>5} {'dup':>5} | {'sent':>5} {'ok':>5} {'rate':>6} {'retry':>6} {'t/o':>5} {'lat_ms':>7}"
    print(header)
    print("-" * len(header))
    for cfg, s in results:
        print(
            f"{cfg.drop_rate:5.2f} {cfg.reorder_rate:5.2f} {cfg.duplicate_rate:5.2f}"
            f" | {s.requests:5} {s.successes:5} {s.success_rate:6.2%}"
            f" {s.retries:6} {s.timeouts:5} {s.mean_latency_ms:7.2f}"
        )


async def main():
    parser = argparse.ArgumentParser(description="MCP transport fault-injection harness")
    parser.add_argument("--drop", type=float, default=None)
    parser.add_argument("--reorder", type=float, default=None)
    parser.add_argument("--duplicate", type=float, default=None)
    parser.add_argument("-n", type=int, default=40, help="requests per scenario")
    args = parser.parse_args()

    if args.drop is not None or args.reorder is not None or args.duplicate is not None:
        cfg = FaultConfig(
            drop_rate=args.drop or 0.0,
            reorder_rate=args.reorder or 0.0,
            duplicate_rate=args.duplicate or 0.0,
        )
        stats = await run_scenario(cfg, n_requests=args.n)
        print(json.dumps(stats.summary(), indent=2))
        return

    # default grid
    scenarios = [
        FaultConfig(),
        FaultConfig(drop_rate=0.1),
        FaultConfig(drop_rate=0.3),
        FaultConfig(drop_rate=0.5),
        FaultConfig(reorder_rate=0.3),
        FaultConfig(reorder_rate=0.5),
        FaultConfig(duplicate_rate=0.3),
        FaultConfig(drop_rate=0.2, reorder_rate=0.2),
        FaultConfig(drop_rate=0.3, reorder_rate=0.2, duplicate_rate=0.1),
    ]

    results = []
    for cfg in scenarios:
        stats = await run_scenario(cfg, n_requests=args.n)
        results.append((cfg, stats))

    print_table(results)


if __name__ == "__main__":
    asyncio.run(main())
