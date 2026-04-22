# mcp-tool-latency-bench

Micro-benchmark measuring the round-trip latency of a minimal JSON-RPC 2.0
tool call across the three MCP transport types: **stdio**, **HTTP**, and
**SSE** (Server-Sent Events).

## What it measures

Each transport sends `N` tool-call requests (`tools/call` → `pong`) to a
local server and records wall-clock round-trip time in milliseconds.  The
benchmark discards a configurable warm-up window before recording.

| Transport | Mechanism | Server side |
|-----------|-----------|-------------|
| stdio     | newline-delimited JSON on stdin/stdout | subprocess pipes |
| http      | HTTP POST → JSON body | `http.server.HTTPServer` |
| sse       | HTTP POST → `text/event-stream` response | same, different `Content-Type` |

> **Note:** this is an *in-process loopback* benchmark.  Numbers reflect IPC
> and local-TCP overhead only, not network latency or model inference time.

## How to run

No external dependencies — pure Python 3.9+ stdlib.

```bash
# full benchmark (100 iterations per transport, default)
python bench.py

# fewer iterations
python bench.py --n 50

# single transport
python bench.py --transport stdio

# run tests
python test_mcp_tool_latency_bench.py
# or
pytest test_mcp_tool_latency_bench.py -v
```

## Sample results (localhost, Linux, Python 3.11)

```
Transport : stdio    median  0.047 ms   p99  0.072 ms
Transport : http     median  0.420 ms   p99  0.741 ms
Transport : sse      median  0.384 ms   p99  0.671 ms
```

### Findings

- **stdio is ~9× faster** than either HTTP transport for a loopback call.
  The dominant cost is pipe write + flush + readline; no TCP stack is
  involved.
- **HTTP and SSE are nearly identical** in latency (~0.4 ms median).  The
  SSE frame overhead (the `data: …\n\n` wrapper) adds no measurable cost
  vs. a plain JSON body.
- In absolute terms all three are fast; at 100 tool calls/s the transport
  contributes < 5 ms total overhead.  Transport choice matters only for
  very high-frequency tool loops (> 1 000 calls/s) where stdio wins
  clearly.

## Scope / out-of-scope

**In scope**
- Loopback IPC/TCP overhead for a trivial payload
- Comparison of transport serialisation formats (plain JSON vs. SSE framing)
- Reproducible, no-dependency micro-benchmark

**Out of scope**
- Real MCP SDK (uses a simplified server; real SDK adds auth, schema
  validation, etc.)
- Network transport (WAN latency, TLS)
- Concurrent/parallel tool calls
- Effect of payload size on throughput
