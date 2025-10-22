"""Base Tool class for agent tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type
from .tool_params import ToolParams


# Type variable for tool parameters
TParams = TypeVar("TParams", bound=ToolParams)


class Tool(ABC, Generic[TParams]):
    """
    Abstract base class for all agent tools.

    Tools define actions that the agent can perform (navigate, click, fill, etc.).
    Each tool has typed parameters (subclass of ToolParams) and provides execution logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name (e.g., "navigate", "click").

        Returns:
            Tool name identifier
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description for LLM context.

        Returns:
            Human-readable description of what the tool does
        """
        pass

    @property
    @abstractmethod
    def params_class(self) -> Type[TParams]:
        """
        Parameters class for this tool.

        Returns:
            ToolParams subclass (e.g., NavigateParams)
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> TParams:
        """
        Validate and parse parameters into typed params object.

        Args:
            parameters: Raw parameters dict from LLM

        Returns:
            Typed params object (e.g., NavigateParams)

        Raises:
            ValidationError: If parameters are invalid
        """
        return self.params_class(**parameters)

    @abstractmethod
    async def execute(self, params: TParams):
        """
        Execute the tool with typed parameters.

        Args:
            params: Typed parameters object

        Returns:
            Execution result
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """
        Convert tool to LLM tool schema format.

        Returns:
            Tool schema for LLM function calling
        """
        # Get Pydantic schema
        params_schema = self.params_class.schema()

        # Extract properties and required
        properties = params_schema.get("properties", {})
        required = params_schema.get("required", [])

        # Clean up properties - remove title fields
        for prop in properties.values():
            prop.pop("title", None)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": properties,
            "required": required,
        }
