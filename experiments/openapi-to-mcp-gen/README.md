# openapi-to-mcp-gen

Toy generator that reads an OpenAPI 3.x spec (JSON or YAML) and emits a
minimal, runnable MCP server stub in Python.

## What it does

For every HTTP operation in the spec the generator produces:

- A `types.Tool` entry with a derived snake-case name, the operation
  description, and a JSON Schema for the inputs (path params, query params,
  and request-body properties are all merged into a single flat schema).
- A `ROUTES` entry that records the HTTP method, base URL, path template,
  and which argument names belong to the path vs the body.
- A `_build_request` helper that substitutes path parameters, collects
  remaining args as query params or a JSON body, and returns a
  `urllib.request.Request`.
- Standard `list_tools` and `call_tool` MCP handlers wired to the route map.

The generated file is self-contained stdlib Python (no third-party deps at
runtime) except for the `mcp` package itself.

## How to run

```bash
pip install pyyaml          # only needed for YAML input
python openapi_to_mcp.py sample_spec.yaml          # print to stdout
python openapi_to_mcp.py sample_spec.yaml --out server.py
```

The generated `server.py` still needs `pip install mcp` to actually run.

Run tests:

```bash
pip install pyyaml pytest
python -m pytest test_generator.py -v
```

## Findings

- Flattening path/query/body params into one schema works for the common
  case. Deeply nested request bodies with `$ref` or `allOf` need a resolver
  step that this generator skips (see Out of scope).
- `operationId` (camelCase or PascalCase) converts cleanly to snake-case
  tool names. Without an `operationId`, the fallback `METHOD_path_segments`
  name is readable but can collide when paths share segment names.
- The generated code calls the live API directly. For real use you would
  want auth header injection and response schema validation.
- Five petstore-style operations end up as five distinct, correctly typed
  tools in under 250 ms on cold start.

## Scope

Covered:
- OpenAPI 3.x paths, parameters (path/query), and simple JSON request bodies.
- OperationId-to-snake-case name derivation.
- Required fields propagated from parameters and requestBody schema.
- Generates valid, compilable Python (verified with `compile()` in tests).

Out of scope:
- `$ref` resolution (components/schemas, external files).
- `allOf` / `oneOf` / `anyOf` merging.
- Authentication (apiKey, OAuth2, Bearer) - add headers manually to the stub.
- OpenAPI 2.x (Swagger).
- Response schema validation.
- Multiple servers or server variables.
