"""Tests for tool_graph_score.py"""

import pytest
from pathlib import Path
from tool_graph_score import ToolGraph, ToolNode, TGCSResult, score_tool_graph, score_manifest_file

DATASETS = Path(__file__).parent / "datasets"


def make_node(name: str, description: str, params: dict | None = None) -> ToolNode:
    return ToolNode(name=name, description=description, params=params or {})


def test_empty_graph_returns_zero():
    result = score_tool_graph(ToolGraph(tools=[]))
    assert result.tgcs == 0.0
    assert result.coverage_score == 0.0


def test_single_tool_no_composability():
    node = make_node("read-data", "Fetch records from the database.", {"id": {"type": "string"}})
    graph = ToolGraph(tools=[node])
    result = score_tool_graph(graph)
    assert result.composability_score == 0.0
    assert result.coverage_score > 0.0
    assert 0.0 < result.tgcs < 1.0


def test_rich_server_outscores_minimal():
    rich = score_manifest_file(DATASETS / "rich_server.json")
    minimal = score_manifest_file(DATASETS / "minimal.json")
    assert rich.tgcs > minimal.tgcs
    assert rich.coverage_score > minimal.coverage_score


def test_filesystem_manifest_has_delete_coverage():
    result = score_manifest_file(DATASETS / "filesystem.json")
    graph = ToolGraph.from_manifest(
        {"tools": [
            {"name": "delete-file", "description": "Delete (remove) a file.", "inputSchema": {"properties": {}}}
        ]}
    )
    cats = graph.tools[0].categories()
    assert "delete" in cats


def test_tgcs_bounded():
    result = score_manifest_file(DATASETS / "rich_server.json")
    assert 0.0 <= result.tgcs <= 1.0
    assert 0.0 <= result.coverage_score <= 1.0
    assert 0.0 <= result.composability_score <= 1.0
    assert 0.0 <= result.quality_score <= 1.0
    assert 0.0 <= result.breadth_score <= 1.0
