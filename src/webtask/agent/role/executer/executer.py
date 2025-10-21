"""Executer role - executes proposed actions."""

from ...action import Action, ActionHistory
from ...tool import ToolRegistry


class Executer:
    """
    Executes proposed actions using registered tools.

    Validates parameters, executes the tool, and records action in history.
    """

    def __init__(self, action_history: ActionHistory, tool_registry: ToolRegistry):
        """
        Initialize executer.

        Args:
            action_history: History to record executed actions
            tool_registry: Registry of available tools
        """
        self.action_history = action_history
        self.tool_registry = tool_registry

    async def execute(self, action: Action) -> None:
        """
        Execute an action.

        Args:
            action: Action to execute

        Raises:
            ValueError: If tool not found or parameters invalid
        """
        # Get tool from registry
        tool = self.tool_registry.get(action.tool_name)

        # Validate and parse parameters
        params = tool.validate_parameters(action.parameters)

        # Execute tool
        await tool.execute(params)

        # Record in history
        self.action_history.add(action)
