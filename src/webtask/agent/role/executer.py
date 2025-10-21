"""Executer role - executes proposed actions."""

from ..step import Action, ExecutionResult
from ..tool import ToolRegistry


class Executer:
    """
    Executes proposed actions using registered tools.

    Returns execution result for step history.
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize executer.

        Args:
            tool_registry: Registry of available tools
        """
        self.tool_registry = tool_registry

    async def execute(self, action: Action) -> ExecutionResult:
        """
        Execute an action.

        Args:
            action: Action to execute

        Returns:
            ExecutionResult with success status and optional error
        """
        try:
            # Get tool from registry
            tool = self.tool_registry.get(action.tool_name)

            # Validate and parse parameters
            params = tool.validate_parameters(action.parameters)

            # Execute tool
            await tool.execute(params)

            return ExecutionResult(success=True)

        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
