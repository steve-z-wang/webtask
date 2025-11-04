"""Proposer mode - proposes actions to take."""

from ...llm import Context, ValidatedLLM
from ..schemas.mode import ProposeResult
from ...prompts import get_prompt
from .base_mode import BaseMode
from ..tool import ToolRegistry
from ..task import Task
from ...llm_browser import LLMBrowser
from ..throttler import Throttler


class Proposer(BaseMode[ProposeResult]):
    """
    Proposer mode suggests actions to take.

    Context includes:
    - Task description
    - Available tools (full schemas)
    - Previous steps
    - Current page state (detailed)

    Returns ProposeResult with actions and next mode suggestion.
    """

    def __init__(
        self,
        validated_llm: ValidatedLLM,
        task_context: Task,
        llm_browser: LLMBrowser,
        throttler: Throttler,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize proposer with tool registry.

        Args:
            validated_llm: LLM wrapper with validation
            task_context: Task state and history
            llm_browser: Browser interface
            throttler: Rate limiter
            tool_registry: Available tools for actions
        """
        super().__init__(validated_llm, task_context, llm_browser, throttler)
        self.tool_registry = tool_registry

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

    async def execute(self) -> ProposeResult:
        """
        Execute propose mode.

        Analyzes current state and proposes actions to take.

        Returns:
            ProposeResult with actions and next mode
        """
        await self.throttler.wait()

        # Build context
        context = await self._build_context()
        self.throttler.update_timestamp()

        # Generate and validate response
        result = await self.validated_llm.generate_validated(
            context, validator=ProposeResult.model_validate
        )

        return result
