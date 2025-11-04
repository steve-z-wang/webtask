"""Proposer role - proposes actions to take."""

from ...llm import Context, ValidatedLLM
from ..schemas.mode import Proposal
from ...prompts import get_prompt
from .base_role import BaseRole
from ..tool import ToolRegistry
from ..task import Task
from ...llm_browser import LLMBrowser
from ...utils.throttler import Throttler


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
        validated_llm: ValidatedLLM,
        task_context: Task,
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        """
        Initialize proposer with its own tool registry.

        Args:
            validated_llm: LLM wrapper with validation
            task_context: Task state and history
            llm_browser: Browser interface
            throttler: Rate limiter
        """
        super().__init__(validated_llm, task_context, llm_browser, throttler)
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
            self.tool_registry.register(
                UploadTool(self.llm_browser, self.task_context)
            )

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

    async def propose_actions(self) -> Proposal:
        """
        Propose actions to take (thinking phase).

        Analyzes current state and proposes browser actions.

        Returns:
            Proposal with browser actions and next mode
        """
        await self.throttler.wait()

        # Build context
        context = await self._build_context()
        self.throttler.update_timestamp()

        # Generate and validate response
        result = await self.validated_llm.generate_validated(
            context, validator=Proposal.model_validate
        )

        return result
