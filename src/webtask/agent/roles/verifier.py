"""Verifier role - checks if task is complete."""

from ...llm import Context
from ..schemas.mode import Proposal
from ...prompts import get_prompt
from .base_role import BaseRole
from ..tool import ToolRegistry


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

    def __init__(self, validated_llm, task_context, llm_browser, throttler):
        """
        Initialize verifier with its own tool registry.

        Args:
            validated_llm: LLM wrapper with validation
            task_context: Task state and history
            llm_browser: Browser interface
            throttler: Rate limiter
        """
        super().__init__(validated_llm, task_context, llm_browser, throttler)
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

    async def propose_actions(self) -> Proposal:
        """
        Propose actions to take (thinking phase).

        Checks if the current page state indicates task completion.
        Proposes mark_complete action if task is done.

        Returns:
            Proposal with mark_complete action if complete
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
