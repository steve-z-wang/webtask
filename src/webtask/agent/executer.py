"""Executer role - executes proposed actions."""

from typing import List
from .step import ExecutionResult
from .schemas import Action
from .tool import ToolRegistry
from .throttler import Throttler


class Executer:
    """Executes proposed actions using registered tools."""

    def __init__(self, tool_registry: ToolRegistry, throttler: Throttler):
        self.tool_registry = tool_registry
        self.throttler = throttler

    async def execute(self, actions: List[Action]) -> List[ExecutionResult]:
        """Execute a list of actions."""
        results = []
        for action in actions:
            try:
                tool = self.tool_registry.get(action.tool)
                # action.parameters is already a validated Pydantic model
                await tool.execute(action.parameters)
                await self.throttler.wait_if_needed()  # Throttle after each action
                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))

        return results
