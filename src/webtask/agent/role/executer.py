"""Executer role - executes proposed actions."""

import time
from typing import List, Optional
from ..step import ExecutionResult
from ..llm_schemas import Action
from ..tool import ToolRegistry
from ...utils import wait


class Executer:
    """Executes proposed actions using registered tools."""

    def __init__(self, tool_registry: ToolRegistry, action_delay: float = 1.0):
        self.tool_registry = tool_registry
        self.action_delay = action_delay
        self.last_action_time: Optional[float] = None

    async def execute(self, actions: List[Action]) -> List[ExecutionResult]:
        """Execute a list of actions."""
        results = []
        for action in actions:
            if self.last_action_time is not None:
                elapsed = time.time() - self.last_action_time
                if elapsed < self.action_delay:
                    await wait(self.action_delay - elapsed)

            try:
                tool = self.tool_registry.get(action.tool)
                # action.parameters is already a validated Pydantic model
                await tool.execute(action.parameters)
                self.last_action_time = time.time()
                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))

        return results
