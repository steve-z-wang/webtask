"""Verifier role - checks if task is complete."""

from typing import TYPE_CHECKING
from ...llm import Context, LLM
from ...prompts import get_prompt
from ..role import BaseRole
from ..tool import ToolRegistry
from ...llm_browser import LLMBrowser
from ...utils.throttler import Throttler

if TYPE_CHECKING:
    from ..task import Task


class VerifierRole(BaseRole):
    """
    Verifier role checks if the task is complete.

    Context includes:
    - Task description
    - Previous steps
    - Current page state
    - mark_complete tool (special tool to signal task completion)

    Returns ModeResult with mark_complete action if task done.
    """

    def __init__(
        self,
        llm: LLM,
        task_context: "Task",
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        """
        Initialize verifier with its own tool registry.

        Args:
            llm: LLM instance for generating responses
            task_context: Task state and history
            llm_browser: Browser interface
            throttler: Rate limiter
        """
        super().__init__(llm, task_context, llm_browser, throttler)
        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register control tools available to Verifier mode."""
        from ..tools.control import MarkCompleteTool

        # Register mark_complete tool for task completion
        self.tool_registry.register(MarkCompleteTool())

    async def _build_context(self) -> Context:
        """Build context for verification with mark_complete tool."""
        system = get_prompt("verifier_system")
        context = Context(system=system)

        # Add task description
        context.append(self.task_context.get_task_context())

        # Add mark_complete tool
        context.append(self.tool_registry.get_tools_context())

        # Add step history
        context.append(self.task_context.get_steps_context())

        # Add current page state
        context.append(await self.llm_browser.get_page_context())

        return context
