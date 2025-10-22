"""Executer role - executes proposed actions."""

from typing import List
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

    async def execute(self, actions: List[Action]) -> List[ExecutionResult]:
        """
        Execute a list of actions.

        Args:
            actions: List of Actions to execute

        Returns:
            List of ExecutionResults with success status and optional errors
        """
        results = []
        for action in actions:
            try:
                # Get tool from registry
                tool = self.tool_registry.get(action.tool_name)

                # Validate and parse parameters
                params = tool.validate_parameters(action.parameters)

                # Execute tool
                await tool.execute(params)

                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))
                # Continue executing remaining actions even if one fails
        
        return results
