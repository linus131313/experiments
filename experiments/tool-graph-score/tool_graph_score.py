"""
Tool Graph Capability Score (TGCS) - measures the capability richness
of an MCP tool set by modelling tools as a directed graph and scoring
coverage, composability, and description quality.

Reference: MCP Governance and Capability Metrics paper (Teklenburg, 2025)
"""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CAPABILITY_CATEGORIES: dict[str, re.Pattern[str]] = {
    "read":      re.compile(r"\b(read|get|fetch|list|retrieve|query|search|find|load|open)\b", re.I),
    "write":     re.compile(r"\b(write|create|update|set|put|post|save|store|insert|add|append)\b", re.I),
    "delete":    re.compile(r"\b(delete|remove|drop|clear|purge|erase)\b", re.I),
    "transform": re.compile(r"\b(transform|convert|parse|format|encode|decode|translate|process)\b", re.I),
    "execute":   re.compile(r"\b(run|execute|call|invoke|trigger|start|launch|eval)\b", re.I),
    "observe":   re.compile(r"\b(watch|monitor|observe|subscribe|listen|stream|log|track)\b", re.I),
}

# Category pairs where src output naturally feeds dst input
_FEED_PAIRS: list[tuple[set[str], set[str]]] = [
    ({"read"},      {"transform", "execute", "write"}),
    ({"transform"}, {"write", "execute"}),
    ({"execute"},   {"observe", "write"}),
    ({"list"},      {"read", "delete"}),
]


@dataclass
class ToolNode:
    name: str
    description: str
    params: dict[str, Any]

    def categories(self) -> set[str]:
        text = f"{self.name} {self.description}"
        return {cat for cat, pat in CAPABILITY_CATEGORIES.items() if pat.search(text)}

    def description_score(self) -> float:
        """0-1 quality heuristic: length, non-placeholder, has params."""
        desc = self.description.strip()
        if not desc or desc.lower() in {"todo", "tbd", "...", "description", ""}:
            return 0.0
        length_score = min(len(desc) / 120.0, 1.0)
        param_score = 1.0 if self.params else 0.5
        return 0.6 * length_score + 0.4 * param_score


@dataclass
class ToolGraph:
    tools: list[ToolNode] = field(default_factory=list)

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any]) -> "ToolGraph":
        nodes: list[ToolNode] = []
        for t in manifest.get("tools", []):
            schema = t.get("inputSchema", {})
            params = schema.get("properties", {})
            nodes.append(ToolNode(
                name=t.get("name", ""),
                description=t.get("description", ""),
                params=params,
            ))
        return cls(tools=nodes)

    def edges(self) -> list[tuple[int, int]]:
        """
        Infer directed edges i->j via category-based feed rules plus
        shared name-token overlap (e.g. read-file -> write-file).
        """
        result: list[tuple[int, int]] = []
        n = len(self.tools)
        for i in range(n):
            for j in range(n):
                if i != j and self._feeds(self.tools[i], self.tools[j]):
                    result.append((i, j))
        return result

    def _feeds(self, src: ToolNode, dst: ToolNode) -> bool:
        sc = src.categories()
        dc = dst.categories()
        if not dc:
            return False
        for src_req, dst_req in _FEED_PAIRS:
            if sc & src_req and dc & dst_req:
                return True
        # Shared resource token: list-files + read-file share "file"
        src_tok = set(re.split(r"[-_]", src.name.lower()))
        dst_tok = set(re.split(r"[-_]", dst.name.lower()))
        shared = src_tok & dst_tok - {"tool", "mcp", ""}
        return bool(shared) and src_tok != dst_tok


@dataclass
class TGCSResult:
    coverage_score: float
    composability_score: float
    quality_score: float
    breadth_score: float
    tgcs: float

    def __str__(self) -> str:
        def bar(v: float) -> str:
            filled = int(v * 20)
            return "#" * filled + "." * (20 - filled)

        return (
            f"Tool Graph Capability Score (TGCS)\n"
            f"  Coverage:      {self.coverage_score:.3f}  [{bar(self.coverage_score)}]\n"
            f"  Composability: {self.composability_score:.3f}  [{bar(self.composability_score)}]\n"
            f"  Quality:       {self.quality_score:.3f}  [{bar(self.quality_score)}]\n"
            f"  Breadth:       {self.breadth_score:.3f}  [{bar(self.breadth_score)}]\n"
            f"  -------\n"
            f"  TGCS:          {self.tgcs:.3f}  [{bar(self.tgcs)}]"
        )


def score_tool_graph(graph: ToolGraph) -> TGCSResult:
    n = len(graph.tools)
    if n == 0:
        return TGCSResult(0.0, 0.0, 0.0, 0.0, 0.0)

    # Coverage: fraction of canonical categories present
    covered: set[str] = set()
    for t in graph.tools:
        covered |= t.categories()
    coverage_score = len(covered) / len(CAPABILITY_CATEGORIES)

    # Composability: directed edge density
    edges = graph.edges()
    max_edges = n * (n - 1)
    composability_score = len(edges) / max_edges if max_edges > 0 else 0.0

    # Quality: average per-tool description score
    quality_score = sum(t.description_score() for t in graph.tools) / n

    # Breadth: log-scaled tool count, saturates at ~20 tools
    breadth_score = min(math.log(n + 1) / math.log(21), 1.0)

    # Weighted aggregate (weights reflect governance paper priorities)
    tgcs = (
        0.35 * coverage_score
        + 0.25 * composability_score
        + 0.20 * quality_score
        + 0.20 * breadth_score
    )

    return TGCSResult(coverage_score, composability_score, quality_score, breadth_score, tgcs)


def score_manifest_file(path: str | Path) -> TGCSResult:
    manifest = json.loads(Path(path).read_text())
    graph = ToolGraph.from_manifest(manifest)
    return score_tool_graph(graph)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute TGCS for one or more MCP tool manifest JSON files"
    )
    parser.add_argument("manifests", nargs="+", metavar="FILE")
    args = parser.parse_args()

    for path in args.manifests:
        result = score_manifest_file(path)
        print(f"\n=== {path} ===")
        print(result)
        print()


if __name__ == "__main__":
    main()
