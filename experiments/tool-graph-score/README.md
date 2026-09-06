# tool-graph-score

Implementation of the Tool Graph Capability Score (TGCS) metric from the
MCP Governance and Capability Metrics paper.

## What it does

TGCS quantifies how capable and composable a set of MCP tools is by
building a directed graph over the tool manifest and computing four
sub-scores:

| Sub-score | Weight | What it measures |
|---|---|---|
| Coverage | 0.35 | Fraction of canonical capability categories (read, write, delete, transform, execute, observe) present |
| Composability | 0.25 | Directed edge density - how often tool outputs can plausibly feed into other tool inputs |
| Quality | 0.20 | Average per-tool description quality (length and param documentation) |
| Breadth | 0.20 | Log-scaled tool count (saturates around 20 tools) |

The final TGCS is a weighted sum in [0, 1].

## How to run

```bash
pip install -r requirements.txt

# Score one or more manifest JSON files
python tool_graph_score.py datasets/minimal.json datasets/filesystem.json datasets/rich_server.json
```

## Sample output

```
=== datasets/filesystem.json ===
Tool Graph Capability Score (TGCS)
  Coverage:      0.500  [##########..........]
  Composability: 0.583  [###########.........]
  Quality:       0.667  [#############.......]
  Breadth:       0.529  [##########..........]
  -------
  TGCS:          0.560  [###########.........]
```

## Findings

- Minimal single-tool servers score around 0.2, dominated by the coverage penalty.
- A well-documented filesystem server (4 tools, distinct categories) scores ~0.56.
- A rich multi-category server (8 tools covering all 6 categories) scores ~0.72.
- Composability is the hardest sub-score to maximise without semantic analysis; the
  heuristic (category feed-pairs + shared name tokens) produces reasonable edges
  but can miss domain-specific chains.

## Running tests

```bash
python -m pytest test_tool_graph_score.py -v
```

5 tests covering empty input, single-tool behaviour, cross-manifest ranking,
category detection, and score bounding.

## Scope

- Pure-Python, no ML or external API calls.
- Edge inference is heuristic (regex on names and category-pair rules).
- Weights match the defaults cited in the governance paper; they can be
  adjusted by changing the constants in `score_tool_graph()`.

## Out of scope

- Semantic embedding-based edge inference (would need a local embedding model).
- Live MCP server introspection (takes a static JSON manifest only).
- Learning weights from a labelled dataset of manifest quality scores.
