"""Base Tool class for agent tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type
from .tool_params import ToolParams


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
