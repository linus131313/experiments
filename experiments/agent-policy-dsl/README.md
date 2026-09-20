# agent-policy-dsl

A tiny YAML DSL for declaring agent tool-use policies, with a Python runtime enforcer.

## What it does

You write a policy file that lists rules for which tool calls an agent is allowed to make. The `PolicyEnforcer` class loads the file and evaluates each tool call against the rules at runtime, returning a structured `Decision` (allowed/denied + reason).

Features:
- Glob patterns for tool names (`exec_*`, `*`)
- Argument-level conditions (`starts_with`, `contains`, `eq`, `lt`, ...)
- Per-tool rate limiting (calls per time window)
- First-match-wins evaluation; unmatched calls default to deny

## How to run

```bash
pip install -r requirements.txt

# Run the enforcer from the CLI against example_policy.yaml
python policy.py example_policy.yaml read_file path=/data/records.csv
# -> ALLOWED: allowed by policy

python policy.py example_policy.yaml read_file path=/etc/shadow
# -> DENIED: denied by policy

python policy.py example_policy.yaml exec_shell cmd=ls
# -> DENIED: denied by policy

# Run tests
python -m pytest test_policy.py -v
```

## Policy format

```yaml
name: my-agent-policy
version: 1
rules:
  - tool: read_file          # glob pattern
    allow: true
    conditions:
      - arg: path            # tool argument name
        op: starts_with      # eq | neq | starts_with | ends_with | contains | lt | gt | lte | gte
        value: /safe/
  - tool: read_file
    allow: false
  - tool: "exec_*"
    allow: false
  - tool: web_search
    allow: true
    rate_limit:
      calls: 5
      window_seconds: 60
  - tool: "*"
    allow: false             # explicit catch-all deny (same as the implicit default)
```

## Findings

- A flat ordered-rule model is enough for most real-world policy requirements without needing boolean logic or nesting.
- Rate limiting over a sliding window catches runaway loops without complex instrumentation.
- Glob matching on tool names makes it easy to blanket-deny a category (`exec_*`, `write_*`).

## Scope

In scope:
- YAML policy parsing and validation
- Tool-name glob matching
- Argument-level conditions on string/numeric values
- Sliding-window rate limiting
- CLI for one-shot checks

Out of scope:
- Policy inheritance or composition across files
- Runtime telemetry or audit logging of decisions
- Integration with any specific agent framework
- Dynamic policy updates without restart
