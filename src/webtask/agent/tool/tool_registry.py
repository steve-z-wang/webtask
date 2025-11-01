"""Tool registry for managing available agent tools."""

import json
from typing import Dict, List, Any
from .tool import Tool
from ...llm import Block


class ToolRegistry:
    """Registry for managing and accessing agent tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def validate_tool_use(self, tool_name: str, parameters: Dict[str, Any]) -> None:
        """Validate that tool exists and parameters are correct."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self._tools[tool_name]
        tool.validate_parameters(parameters)

    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def get_all(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Clear all registered tools from the registry."""
        self._tools.clear()

    def get_tools_context(self) -> Block:
        """Get formatted tools context for LLM."""
        schemas = [tool.to_schema() for tool in self._tools.values()]
        return Block(f"Tools:\n{json.dumps(schemas, indent=2)}")
