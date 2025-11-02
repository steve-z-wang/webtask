"""Base Tool class for agent tools."""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type, List
from .schemas import ToolParams
from ..llm import Block


TParams = TypeVar("TParams", bound=ToolParams)


class Tool(ABC, Generic[TParams]):
    """Abstract base class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    @abstractmethod
    def params_class(self) -> Type[TParams]:
        """Parameters class for this tool."""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> TParams:
        """Validate and parse parameters into typed params object."""
        return self.params_class(**parameters)

    @abstractmethod
    async def execute(self, params: TParams):
        """Execute the tool with typed parameters."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to LLM tool schema format."""
        params_schema = self.params_class.schema()
        properties = params_schema.get("properties", {})
        required = params_schema.get("required", [])

        for prop in properties.values():
            prop.pop("title", None)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": properties,
            "required": required,
        }


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
