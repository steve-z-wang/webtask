"""Unit tests for JSON schema utilities."""

import pytest
from webtask._internal.llm.json_schema_utils import resolve_json_schema_refs

pytestmark = pytest.mark.unit


@pytest.mark.unit
def test_resolve_json_schema_refs_with_nested_model():
    """Test that $ref references are resolved correctly for nested models."""
    # Schema with $ref (typical output from Pydantic's model_json_schema())
    schema_with_refs = {
        "$defs": {
            "Item": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Item name"},
                    "quantity": {"type": "integer", "description": "Quantity"},
                },
                "required": ["name", "quantity"],
            }
        },
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"$ref": "#/$defs/Item"}},
            "total": {"type": "integer"},
        },
        "required": ["items", "total"],
    }

    # Resolve refs
    resolved = resolve_json_schema_refs(schema_with_refs)

    # Verify $defs is removed
    assert "$defs" not in resolved

    # Verify $ref is resolved inline
    assert resolved["properties"]["items"]["items"]["type"] == "object"
    assert (
        resolved["properties"]["items"]["items"]["properties"]["name"]["type"]
        == "string"
    )
    assert (
        resolved["properties"]["items"]["items"]["properties"]["quantity"]["type"]
        == "integer"
    )
    assert resolved["properties"]["items"]["items"]["required"] == ["name", "quantity"]

    # Verify other fields are preserved
    assert resolved["type"] == "object"
    assert resolved["properties"]["total"]["type"] == "integer"
    assert resolved["required"] == ["items", "total"]
