"""Tool registry for managing available agent tools."""

from typing import Dict, List, Any
from .tool import Tool


class ToolRegistry:
    """
    Registry for managing and accessing agent tools.

    Maintains a collection of tools and provides their schemas as context for LLM.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def validate_tool_use(self, tool_name: str, parameters: Dict[str, Any]) -> None:
        """
        Validate that tool exists and parameters are correct.

        Args:
            tool_name: Tool name
            parameters: Tool parameters

        Raises:
            ValueError: If tool doesn't exist or parameters are invalid
        """
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self._tools[tool_name]
        tool.validate_parameters(parameters)  # Raises if invalid

    def get(self, name: str) -> Tool:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            KeyError: If tool is not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def get_all(self) -> List[Tool]:
        """
        Get all registered tools.

        Returns:
            List of all registered tools
        """
        return list(self._tools.values())

    def get_context_string(self) -> str:
        """
        Get context string with all tool schemas for LLM.

        Returns:
            JSON-formatted string of tool schemas
        """
        import json
        schemas = [tool.to_schema() for tool in self._tools.values()]
        return json.dumps(schemas, indent=2)
