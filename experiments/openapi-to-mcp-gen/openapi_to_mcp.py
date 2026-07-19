#!/usr/bin/env python3
"""
openapi_to_mcp.py - Generate a minimal MCP server stub from an OpenAPI 3.x spec.

Usage:
    python openapi_to_mcp.py spec.yaml --out server.py
    python openapi_to_mcp.py spec.json           # prints to stdout
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Spec loading
# ---------------------------------------------------------------------------

def load_spec(path: str) -> dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        if not HAS_YAML:
            sys.exit("pyyaml required for YAML input: pip install pyyaml")
        return yaml.safe_load(text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Name derivation
# ---------------------------------------------------------------------------

_UC_BOUND = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL = re.compile(r"([a-z\d])([A-Z])")


def _snake(name: str) -> str:
    s = _UC_BOUND.sub(r"\1_\2", name)
    s = _CAMEL.sub(r"\1_\2", s)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _tool_name(method: str, path: str, operation_id: str | None) -> str:
    if operation_id:
        return _snake(operation_id)[:64]
    parts = [
        re.sub(r"[{}]", "", seg)
        for seg in path.strip("/").split("/")
        if seg and seg not in ("api", "v1", "v2", "v3")
    ]
    return f"{method}_{'_'.join(parts)}"[:64].rstrip("_")


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _param_schema(param: dict[str, Any]) -> dict[str, Any]:
    raw = param.get("schema", {})
    out: dict[str, Any] = {}
    if raw.get("type"):
        out["type"] = raw["type"]
    desc = param.get("description") or raw.get("description")
    if desc:
        out["description"] = desc
    for key in ("enum", "default", "minimum", "maximum"):
        if key in raw:
            out[key] = raw[key]
    return out or {"type": "string"}


def _body_props(request_body: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return (properties dict, required list) extracted from a requestBody."""
    content = request_body.get("content", {})
    schema: dict[str, Any] = {}
    for mime in ("application/json", "application/x-www-form-urlencoded"):
        if mime in content:
            schema = content[mime].get("schema", {})
            break
    if not schema:
        for v in content.values():
            schema = v.get("schema", {})
            break

    if schema.get("type") == "object" and "properties" in schema:
        props = {
            k: {kk: vv for kk, vv in v.items()
                if kk in ("type", "description", "enum", "default", "items", "format")}
            for k, v in schema["properties"].items()
        }
        return props, schema.get("required", [])

    # Non-object body: single 'body' parameter
    req = ["body"] if request_body.get("required") else []
    return {"body": {"type": "string", "description": "Request body (JSON-encoded)"}}, req


# ---------------------------------------------------------------------------
# Tool extraction
# ---------------------------------------------------------------------------

def extract_tools(spec: dict[str, Any]) -> list[dict[str, Any]]:
    servers = spec.get("servers", [])
    base_url = servers[0].get("url", "").rstrip("/") if servers else ""
    tools: list[dict[str, Any]] = []

    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        shared: dict[str, Any] = {p["name"]: p for p in path_item.get("parameters", []) if "name" in p}

        for method in ("get", "post", "put", "patch", "delete"):
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue

            name = _tool_name(method, path, op.get("operationId"))
            desc = (op.get("description") or op.get("summary") or f"{method.upper()} {path}").strip()

            param_map = dict(shared)
            for p in op.get("parameters", []):
                if "name" in p:
                    param_map[p["name"]] = p

            properties: dict[str, Any] = {}
            required: list[str] = []
            path_params: list[str] = []
            body_params: list[str] = []

            for param in param_map.values():
                loc = param.get("in")
                if loc not in ("path", "query", "header"):
                    continue
                pname = param["name"]
                properties[pname] = _param_schema(param)
                if param.get("required") or loc == "path":
                    required.append(pname)
                if loc == "path":
                    path_params.append(pname)

            rb = op.get("requestBody")
            if rb:
                bp, br = _body_props(rb)
                body_params = list(bp.keys())
                properties.update(bp)
                required.extend(r for r in br if r not in required)

            input_schema: dict[str, Any] = {"type": "object", "properties": properties}
            if required:
                input_schema["required"] = required

            tools.append({
                "name": name,
                "description": desc,
                "input_schema": input_schema,
                "method": method.upper(),
                "base_url": base_url,
                "path": path,
                "path_params": path_params,
                "body_params": body_params,
            })

    return tools


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def render_stub(spec: dict[str, Any], tools: list[dict[str, Any]]) -> str:
    info = spec.get("info", {})
    title = info.get("title", "Generated API")
    version = info.get("version", "unknown")
    server_name = re.sub(r"[^a-z0-9-]", "-", title.lower()).strip("-")

    tool_lines: list[str] = []
    for t in tools:
        schema_json = json.dumps(t["input_schema"], indent=4)
        indented = "\n".join("        " + ln for ln in schema_json.splitlines())
        desc = t["description"].replace("\\", "\\\\").replace('"', '\\"')
        tool_lines += [
            "    types.Tool(",
            f'        name="{t["name"]}",',
            f'        description="{desc}",',
            f"        inputSchema={indented},",
            "    ),",
        ]

    route_lines: list[str] = []
    for t in tools:
        route_lines += [
            f'    "{t["name"]}": {{',
            f'        "method": "{t["method"]}",',
            f'        "base_url": "{t["base_url"]}",',
            f'        "path": "{t["path"]}",',
            f'        "path_params": {json.dumps(t["path_params"])},',
            f'        "body_params": {json.dumps(t["body_params"])},',
            "    },",
        ]

    tools_block = "\n".join(tool_lines)
    routes_block = "\n".join(route_lines)

    return f'''\
"""MCP server stub - auto-generated from "{title}" v{version}."""

import asyncio
import json
import urllib.parse
import urllib.request
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("{server_name}")

TOOLS: list[types.Tool] = [
{tools_block}
]

ROUTES: dict[str, dict[str, Any]] = {{
{routes_block}
}}


def _build_request(
    route: dict[str, Any], args: dict[str, Any]
) -> tuple[str, bytes | None]:
    path = route["path"]
    for pname in route["path_params"]:
        if pname in args:
            path = path.replace("{{" + pname + "}}", urllib.parse.quote(str(args[pname])))
    query = {{
        k: v for k, v in args.items()
        if k not in route["path_params"] and k not in route["body_params"]
    }}
    url = route["base_url"] + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    body: bytes | None = None
    if route["method"] in ("POST", "PUT", "PATCH") and route["body_params"]:
        body_data = {{k: args[k] for k in route["body_params"] if k in args}}
        body = json.dumps(body_data).encode()
    return url, body


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name not in ROUTES:
        raise ValueError(f"Unknown tool: {{name}}")
    route = ROUTES[name]
    url, body = _build_request(route, arguments)
    req = urllib.request.Request(url, data=body, method=route["method"])
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        text = f"Error calling {{url}}: {{exc}}"
    return [types.TextContent(type="text", text=text)]


async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_main())
'''


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a minimal MCP server stub from an OpenAPI 3.x spec."
    )
    parser.add_argument("spec", help="Path to OpenAPI spec (JSON or YAML)")
    parser.add_argument("--out", default="-", help="Output file (default: stdout)")
    a = parser.parse_args()

    spec = load_spec(a.spec)
    tools = extract_tools(spec)
    if not tools:
        print("Warning: no operations found in spec", file=sys.stderr)
    stub = render_stub(spec, tools)

    if a.out == "-":
        print(stub)
    else:
        Path(a.out).write_text(stub, encoding="utf-8")
        print(f"Wrote {len(tools)} tool(s) to {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
