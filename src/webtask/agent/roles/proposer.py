"""Proposer role - proposes actions to take."""

from typing import TYPE_CHECKING
from ...llm import Context, LLM
from ...prompts import get_prompt
from ..role import BaseRole
from ..tool import ToolRegistry
from ...llm_browser import LLMBrowser
from ...utils.throttler import Throttler

if TYPE_CHECKING:
    from ..task import Task


class ProposerRole(BaseRole):
    """
    Proposer role suggests actions to take.

    Context includes:
    - Task description
    - Available browser action tools (navigate, click, fill, type, upload)
    - Previous steps
    - Current page state (detailed)

    Returns ModeResult with browser actions and next mode suggestion.
    """

    def __init__(
        self,
        llm: LLM,
        task_context: "Task",
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        """
        Initialize proposer with its own tool registry.

        Args:
            llm: LLM instance for generating responses
            task_context: Task state and history
            llm_browser: Browser interface
            throttler: Rate limiter
        """
        super().__init__(llm, task_context, llm_browser, throttler)
        self.llm_browser = llm_browser
        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register browser action tools available to Proposer mode."""
        from ..tools.browser import (
            NavigateTool,
            ClickTool,
            FillTool,
            TypeTool,
            UploadTool,
        )

        # Register browser action tools
        self.tool_registry.register(NavigateTool(self.llm_browser))
        self.tool_registry.register(ClickTool(self.llm_browser))
        self.tool_registry.register(FillTool(self.llm_browser))
        self.tool_registry.register(TypeTool(self.llm_browser))

        # Register upload tool if task has resources
        if self.task_context.resources:
            self.tool_registry.register(UploadTool(self.llm_browser, self.task_context))

    async def _build_context(self) -> Context:
        """Build full context for proposing actions."""
        system = get_prompt("proposer_system")
        context = Context(system=system)

        # Add task description
        context.append(self.task_context.get_task_context())

        # Add available tools with full schemas
        context.append(self.tool_registry.get_tools_context())

        # Add step history
        context.append(self.task_context.get_steps_context())

        # Add current page state
        context.append(await self.llm_browser.get_page_context())

        return context
