"""
Tiny DSL for declaring agent tool-use policies with a runtime enforcer.

Policy files are YAML. Rules are evaluated top-to-bottom; first match wins.
Unmatched calls default to deny.
"""

import fnmatch
import time
import yaml
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Condition:
    arg: str
    op: str   # eq | neq | starts_with | ends_with | contains | lt | gt | lte | gte
    value: Any


@dataclass
class RateLimit:
    calls: int
    window_seconds: int


@dataclass
class Rule:
    tool: str           # glob pattern (e.g. "exec_*" or "*")
    allow: bool
    conditions: List[Condition] = field(default_factory=list)
    rate_limit: Optional[RateLimit] = None


@dataclass
class Decision:
    allowed: bool
    reason: str
    rule_matched: Optional[str] = None


def _parse_rules(rules_data: list) -> List[Rule]:
    rules = []
    for r in rules_data:
        conditions = [
            Condition(arg=c["arg"], op=c["op"], value=c["value"])
            for c in r.get("conditions", [])
        ]
        rate_limit = None
        if "rate_limit" in r:
            rl = r["rate_limit"]
            rate_limit = RateLimit(
                calls=rl["calls"], window_seconds=rl["window_seconds"]
            )
        rules.append(
            Rule(
                tool=r["tool"],
                allow=bool(r["allow"]),
                conditions=conditions,
                rate_limit=rate_limit,
            )
        )
    return rules


def _check_conditions(conditions: List[Condition], args: Dict[str, Any]) -> bool:
    for cond in conditions:
        val = args.get(cond.arg)
        if val is None:
            return False
        s = str(val)
        op = cond.op
        v = cond.value
        if op == "eq" and val != v:
            return False
        elif op == "neq" and val == v:
            return False
        elif op == "starts_with" and not s.startswith(v):
            return False
        elif op == "ends_with" and not s.endswith(v):
            return False
        elif op == "contains" and v not in s:
            return False
        elif op == "lt" and not (val < v):
            return False
        elif op == "gt" and not (val > v):
            return False
        elif op == "lte" and not (val <= v):
            return False
        elif op == "gte" and not (val >= v):
            return False
    return True


class PolicyEnforcer:
    """Parse a YAML policy file and enforce it against tool calls."""

    def __init__(self, policy_path: str):
        with open(policy_path) as f:
            data = yaml.safe_load(f)
        self.name: str = data.get("name", "unnamed")
        self.rules: List[Rule] = _parse_rules(data.get("rules", []))
        # tool_name -> list of monotonic timestamps for rate limiting
        self._timestamps: Dict[str, List[float]] = defaultdict(list)

    def check(self, tool_name: str, args: Dict[str, Any]) -> Decision:
        """Return a Decision for the given tool call."""
        for rule in self.rules:
            if not fnmatch.fnmatch(tool_name, rule.tool):
                continue
            if not _check_conditions(rule.conditions, args):
                continue
            if rule.allow and rule.rate_limit:
                if not self._within_rate_limit(tool_name, rule.rate_limit):
                    return Decision(
                        allowed=False,
                        reason=(
                            f"rate limit exceeded: {rule.rate_limit.calls} calls"
                            f" per {rule.rate_limit.window_seconds}s"
                        ),
                        rule_matched=rule.tool,
                    )
            if rule.allow:
                self._record(tool_name)
            return Decision(
                allowed=rule.allow,
                reason="allowed by policy" if rule.allow else "denied by policy",
                rule_matched=rule.tool,
            )
        return Decision(allowed=False, reason="no matching rule (default deny)")

    def _within_rate_limit(self, tool: str, rl: RateLimit) -> bool:
        now = time.monotonic()
        cutoff = now - rl.window_seconds
        self._timestamps[tool] = [t for t in self._timestamps[tool] if t > cutoff]
        return len(self._timestamps[tool]) < rl.calls

    def _record(self, tool: str) -> None:
        self._timestamps[tool].append(time.monotonic())


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: policy.py <policy.yaml> <tool_name> [key=value ...]")
        sys.exit(1)

    policy_path, tool_name = sys.argv[1], sys.argv[2]
    args: Dict[str, Any] = {}
    for kv in sys.argv[3:]:
        k, v = kv.split("=", 1)
        args[k] = v

    enforcer = PolicyEnforcer(policy_path)
    decision = enforcer.check(tool_name, args)
    label = "ALLOWED" if decision.allowed else "DENIED"
    print(f"{label}: {decision.reason}")
    if decision.rule_matched:
        print(f"  matched rule: {decision.rule_matched}")
    sys.exit(0 if decision.allowed else 1)
