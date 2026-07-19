"""Tests for openapi_to_mcp.py generator."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import openapi_to_mcp as gen

PETSTORE: dict = {
    "openapi": "3.0.3",
    "info": {"title": "Pet Store", "version": "1.0.0"},
    "servers": [{"url": "https://petstore.example.com/v1"}],
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Max items",
                        "schema": {"type": "integer", "default": 20},
                    },
                    {
                        "name": "tag",
                        "in": "query",
                        "schema": {"type": "string"},
                    },
                ],
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string", "description": "Pet name"},
                                    "tag": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "showPetById",
                "summary": "Info for a specific pet",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "Pet ID",
                        "schema": {"type": "string"},
                    }
                ],
            }
        },
    },
}


def test_tool_count():
    tools = gen.extract_tools(PETSTORE)
    assert len(tools) == 3


def test_tool_names():
    tools = gen.extract_tools(PETSTORE)
    names = {t["name"] for t in tools}
    assert "list_pets" in names
    assert "create_pet" in names
    assert "show_pet_by_id" in names


def test_path_param_required():
    tools = gen.extract_tools(PETSTORE)
    show = next(t for t in tools if t["name"] == "show_pet_by_id")
    assert "petId" in show["path_params"]
    assert "petId" in show["input_schema"].get("required", [])


def test_body_params_extracted():
    tools = gen.extract_tools(PETSTORE)
    create = next(t for t in tools if t["name"] == "create_pet")
    assert "name" in create["body_params"]
    assert "name" in create["input_schema"].get("required", [])
    assert "tag" in create["input_schema"]["properties"]


def test_stub_renders_valid_python():
    tools = gen.extract_tools(PETSTORE)
    stub = gen.render_stub(PETSTORE, tools)
    # Should compile without errors
    compile(stub, "<stub>", "exec")
    assert 'Server("pet-store")' in stub
    assert "list_pets" in stub
    assert "show_pet_by_id" in stub
    assert "ROUTES" in stub
    assert "TOOLS" in stub
