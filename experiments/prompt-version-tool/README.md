# prompt-version-tool

Git-native tool for versioning prompts with diffable test cases per version.

## What it does

`pvt.py` stores prompt files inside a `.prompts/` directory committed to git.
Each prompt lives at `.prompts/<slug>/prompt.txt`. Alongside the prompt you can
place a `tests.yaml` file that defines structural invariants (things that must
be true about the prompt text itself). Versioning is handled entirely by git -
every `pvt save` creates a real commit, so `pvt diff` and `pvt log` delegate to
`git diff` and `git log`.

The test runner checks structural properties without calling any LLM:

| Type | Checks |
|---|---|
| `contains` | substring must be present |
| `not_contains` | substring must be absent |
| `starts_with` | prompt must begin with prefix |
| `regex` | MULTILINE regex must match |
| `max_chars` | character count at or below threshold |
| `min_chars` | character count at or above threshold |
| `max_lines` | line count at or below threshold |

## How to run

```bash
pip install pyyaml

# one-time setup inside a git repo
python pvt.py init

# save a prompt
echo "You are a helpful assistant. Always respond in JSON." | python pvt.py save json-assistant
# or from a file
python pvt.py save json-assistant -f my_prompt.txt -m "tighten persona"

# list prompts
python pvt.py list

# show history
python pvt.py log json-assistant

# diff two versions (any git refs)
python pvt.py diff json-assistant HEAD~1 HEAD

# run structural tests
python pvt.py test json-assistant
```

### tests.yaml example

```yaml
tests:
  - name: must include persona
    type: starts_with
    value: "You are"
  - name: must request JSON
    type: contains
    value: JSON
  - name: no leaked credentials
    type: not_contains
    value: sk-
  - name: reasonable length
    type: max_chars
    value: 2000
  - name: role line present
    type: regex
    value: "^You are a \\w+"
```

## Run the tests

```bash
pytest test_pvt.py -v    # 19 tests, no network or LLM needed
```

## Findings

- Using git as the versioning backend is zero-cost and gives full history,
  blame, and diffing for free. No custom storage format needed.
- Structural tests (invariants on the prompt text) catch accidental deletions
  early - for example removing "respond in JSON" while editing an unrelated
  section.
- Keeping tests alongside the prompt in git means test expectations are
  versioned too, so you can see when the bar was raised or lowered.
- The regex type covers most complex structural checks without adding
  dependencies.

## Scope

- Single-file prompts (`.txt`). Templates with variables are out of scope.
- Structural tests only - no LLM evaluation.
- Requires an existing git repo.

## Out of scope

- LLM-based evaluation (comparing actual model outputs across versions).
- Multi-user conflict resolution beyond what git provides.
- Prompt templates or variable interpolation.
- Remote-hosted prompt registries.
