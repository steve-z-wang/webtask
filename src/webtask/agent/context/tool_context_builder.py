"""Context builder for ToolRegistry."""

import json
from typing import TYPE_CHECKING
from ...llm import Block

if TYPE_CHECKING:
    from ..tool import ToolRegistry


class ToolContextBuilder:
    """Builds LLM context blocks from ToolRegistry."""

    def __init__(self, tool_registry: "ToolRegistry"):
        self._tool_registry = tool_registry

    def build_tools_context(self) -> Block:
        """Get formatted tools context for LLM."""
        schemas = []
        for tool in self._tool_registry.get_all():
            # Get Pydantic schema from tool.Params
            params_schema = tool.Params.model_json_schema()
            properties = params_schema.get("properties", {})
            required = params_schema.get("required", [])

            # Remove title from properties for cleaner schema
            for prop in properties.values():
                prop.pop("title", None)

            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": properties,
                "required": required,
            })

        return Block(heading="Available Tools", content=json.dumps(schemas, indent=2))
