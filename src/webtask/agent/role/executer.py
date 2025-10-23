"""Executer role - executes proposed actions."""

import time
from typing import List, Optional
from ..step import Action, ExecutionResult
from ..tool import ToolRegistry
from ...utils import wait


class Executer:
    """
    Executes proposed actions using registered tools.

    Returns execution result for step history.
    """

    def __init__(self, tool_registry: ToolRegistry, action_delay: float = 1.0):
        """
        Initialize executer.

        Args:
            tool_registry: Registry of available tools
            action_delay: Minimum delay in seconds between actions (default: 1.0)
        """
        self.tool_registry = tool_registry
        self.action_delay = action_delay
        self.last_action_time: Optional[float] = None

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
            # Ensure minimum delay between actions
            if self.last_action_time is not None:
                elapsed = time.time() - self.last_action_time
                if elapsed < self.action_delay:
                    await wait(self.action_delay - elapsed)

            try:
                # Get tool from registry
                tool = self.tool_registry.get(action.tool_name)

                # Validate and parse parameters
                params = tool.validate_parameters(action.parameters)

                # Execute tool
                await tool.execute(params)

                # Record action time
                self.last_action_time = time.time()

                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))
                # Continue executing remaining actions even if one fails

        return results
