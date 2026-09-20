import os
import tempfile

import pytest
import yaml

from policy import PolicyEnforcer


def make_enforcer(rules: list, name: str = "test") -> PolicyEnforcer:
    data = {"name": name, "rules": rules}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        return PolicyEnforcer(path)
    finally:
        os.unlink(path)


def test_allow_by_tool_name():
    e = make_enforcer([{"tool": "read_file", "allow": True}])
    d = e.check("read_file", {"path": "/anywhere"})
    assert d.allowed
    assert d.rule_matched == "read_file"


def test_deny_by_tool_name():
    e = make_enforcer([{"tool": "write_file", "allow": False}])
    d = e.check("write_file", {"path": "/anywhere"})
    assert not d.allowed


def test_condition_starts_with_allow_and_deny():
    rules = [
        {
            "tool": "read_file",
            "allow": True,
            "conditions": [{"arg": "path", "op": "starts_with", "value": "/safe/"}],
        },
        {"tool": "read_file", "allow": False},
    ]
    e = make_enforcer(rules)
    assert e.check("read_file", {"path": "/safe/data.csv"}).allowed
    assert not e.check("read_file", {"path": "/etc/passwd"}).allowed


def test_glob_pattern_denies_multiple_tools():
    e = make_enforcer([{"tool": "exec_*", "allow": False}])
    assert not e.check("exec_shell", {}).allowed
    assert not e.check("exec_python", {}).allowed
    # Non-matching tool falls through to default deny
    assert not e.check("read_file", {}).allowed


def test_default_deny_when_no_rules_match():
    e = make_enforcer([])
    d = e.check("any_tool", {})
    assert not d.allowed
    assert "default deny" in d.reason


def test_rate_limit_blocks_after_threshold():
    rules = [
        {
            "tool": "web_search",
            "allow": True,
            "rate_limit": {"calls": 3, "window_seconds": 60},
        }
    ]
    e = make_enforcer(rules)
    for _ in range(3):
        assert e.check("web_search", {}).allowed
    blocked = e.check("web_search", {})
    assert not blocked.allowed
    assert "rate limit" in blocked.reason


def test_example_policy_file():
    policy_path = os.path.join(os.path.dirname(__file__), "example_policy.yaml")
    e = PolicyEnforcer(policy_path)
    assert e.check("read_file", {"path": "/data/records.csv"}).allowed
    assert not e.check("read_file", {"path": "/etc/shadow"}).allowed
    assert not e.check("write_file", {"path": "/data/out.csv"}).allowed
    assert not e.check("exec_shell", {"cmd": "ls"}).allowed
    assert e.check("web_search", {"query": "python"}).allowed
