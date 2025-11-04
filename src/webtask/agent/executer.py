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
                # Throttle before action
                await self.throttler.wait()
                # action.parameters is already a validated Pydantic model
                await tool.execute(action.parameters)
                # Update timestamp after action completes
                self.throttler.update_timestamp()
                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))

        return results
