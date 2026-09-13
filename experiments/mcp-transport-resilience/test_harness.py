"""Tests for mcp-transport-resilience harness."""
import asyncio
import pytest
from harness import FaultConfig, FaultProxy, MCPClient, MockMCPServer, RunStats, run_scenario


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_run_stats_success_rate_empty():
    s = RunStats()
    assert s.success_rate == 0.0
    assert s.mean_latency_ms == 0.0


def test_run_stats_success_rate():
    s = RunStats(requests=10, successes=7)
    assert abs(s.success_rate - 0.7) < 1e-9


@pytest.mark.asyncio
async def test_no_faults_full_success():
    cfg = FaultConfig(seed=1)
    stats = await run_scenario(cfg, n_requests=20)
    assert stats.success_rate == 1.0
    assert stats.retries == 0
    assert stats.timeouts == 0


@pytest.mark.asyncio
async def test_high_drop_degrades_success():
    cfg = FaultConfig(drop_rate=0.9, seed=42)
    stats = await run_scenario(cfg, n_requests=20)
    # With 90% drop and 3 retries, some requests will still fail
    assert stats.success_rate < 1.0
    assert stats.retries > 0


@pytest.mark.asyncio
async def test_retries_kick_in_under_drops():
    cfg_no_fault = FaultConfig(seed=5)
    cfg_with_drop = FaultConfig(drop_rate=0.4, seed=5)
    s_clean = await run_scenario(cfg_no_fault, n_requests=20)
    s_drop = await run_scenario(cfg_with_drop, n_requests=20)
    # retries should be higher when drops occur
    assert s_drop.retries >= s_clean.retries
    assert s_drop.timeouts >= s_clean.timeouts


@pytest.mark.asyncio
async def test_mock_server_echo():
    inbox: asyncio.Queue = asyncio.Queue()
    outbox: asyncio.Queue = asyncio.Queue()
    server = MockMCPServer(inbox, outbox)
    asyncio.create_task(server.run())

    await inbox.put({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "echo", "arguments": {"text": "hello"}}})
    resp = await asyncio.wait_for(outbox.get(), timeout=1.0)
    import json
    result = json.loads(resp["result"]["content"][0]["text"])
    assert result["echoed"] == "hello"

    await inbox.put(None)
