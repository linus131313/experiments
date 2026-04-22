# Skipped Monthly Repo Notes

## 2026-04-22 — mcp-governance-toolkit

**Theme:** `mcp-governance-toolkit — CLI + library for auditing MCP servers (schema lint + security checks + score)`

**Why skipped (not created as public repo):**

The scaffold was built successfully and all 20 tests pass locally (`/tmp/mcp-governance-toolkit/`), but publishing the repo to GitHub could not be completed due to environment constraints:

1. `mcp__github__create_repository` returned HTTP 403 — the GitHub MCP integration is scoped read-only to `linus131313/experiments` and does not have permission to create new repositories.
2. `git push` via the local git proxy (`http://local_proxy@127.0.0.1:35149/git/…`) returned `502: repository not authorized` for any repo other than `experiments`.
3. No `gh` CLI is available in the environment.

**What was built (ready to publish when env allows):**

- `pyproject.toml`, `LICENSE` (MIT), thorough `README.md`
- `src/mcp_governance/` — `models.py`, `linter.py`, `security.py`, `scorer.py`, `cli.py`
- `tests/` — 20 passing unit tests covering all three check modules
- `examples/good_server.json` and `examples/risky_server.json`
- 4 logical git commits in `/tmp/mcp-governance-toolkit/`

**To publish manually:**

```bash
cp -r /tmp/mcp-governance-toolkit ~/mcp-governance-toolkit
cd ~/mcp-governance-toolkit
gh repo create linus131313/mcp-governance-toolkit --public \
  --description "CLI + library for auditing MCP server schemas (schema lint, security checks, capability score)" \
  --source=. --push
```
