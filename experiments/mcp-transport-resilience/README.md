# mcp-transport-resilience

Fault-injection harness for MCP-style JSON-RPC transport. Simulates drop,
reorder, and duplicate faults on in-process message queues modelling an MCP
stdio channel, then measures how a retrying client recovers.

## What it does

The harness wires together three components over asyncio queues:

```
Client --> FaultProxy --> MockMCPServer
Client <--             <-- MockMCPServer
```

**FaultProxy** - applies three independent fault types on the request path:
- **drop**: message silently discarded (models network loss or stdio truncation)
- **reorder**: message delayed by a configurable number of milliseconds (models
  out-of-order delivery)
- **duplicate**: message sent twice (models retransmission or double-delivery)

**MockMCPServer** - minimal JSON-RPC 2.0 server supporting `initialize` and
`tools/call` for two toy tools (`echo`, `add`).

**MCPClient** - sends requests and retries on timeout (up to 3 retries,
150 ms timeout). Records success rate, retry count, and latency.

## How to run

```bash
# install test dependency
pip install pytest pytest-asyncio

# default scenario grid (9 fault configurations, 40 requests each)
python harness.py

# single run with 30% drop rate
python harness.py --drop 0.3

# combined faults
python harness.py --drop 0.2 --reorder 0.3

# run tests
python -m pytest test_harness.py -v
```

## Findings

Results from `python harness.py` (40 requests per scenario, seed=42):

```
 drop reord   dup |  sent    ok   rate  retry   t/o  lat_ms
-----------------------------------------------------------
 0.00  0.00  0.00 |    41    41 100.00%      0     0    0.07
 0.10  0.00  0.00 |    41    41 100.00%      7     7   25.73
 0.30  0.00  0.00 |    41    40  97.56%     20    21   64.27
 0.50  0.00  0.00 |    41    38  92.68%     39    42  119.02
 0.00  0.30  0.00 |    41    41 100.00%      0     0   23.56
 0.00  0.50  0.00 |    41    41 100.00%      0     0   37.28
 0.00  0.00  0.30 |    41    41 100.00%      0     0    0.04
 0.20  0.20  0.00 |    41    41 100.00%     10    10   50.42
 0.30  0.20  0.10 |    41    40  97.56%     23    24   85.27
```

Key observations:

- **Reorder and duplicate alone never caused failures.** Reorder adds latency
  (the delayed message still arrives within the retry window) and duplicate
  messages are ignored by the response dispatcher (matched by request id).

- **Drops are the only fault that causes actual failures.** With 3 retries,
  the client tolerates a 10% drop rate with zero failures; at 30% it starts
  losing about 2.5% of requests; at 50% it loses around 7%.

- **Retry cost is steep.** At 30% drop rate the client issues 20 extra
  requests (50% overhead) and average latency rises from 0.07ms to 64ms.
  At 50% drop the overhead is nearly 100% (39 retries for 41 requests).

- **Combined faults stack linearly.** The 30%+20%+10% mixed scenario shows
  roughly the sum of the individual costs - no unexpected interaction.

## Scope

- All transport I/O is simulated with asyncio queues (no real stdio or network).
- Faults are applied only on the client-to-server path; the response path is
  always clean (simulating a server-acks-all model).
- The mock server never crashes - only message delivery is disrupted.
- No real MCP SDK dependency; the JSON-RPC format matches the 2024-11-05
  MCP protocol spec structure but is not validated against it.

## Out of scope

- Real stdio/SSE/HTTP transport faults
- Server-side crash and reconnect scenarios
- Bidirectional fault injection (response drops)
- Larger payload sizes and their effect on latency
