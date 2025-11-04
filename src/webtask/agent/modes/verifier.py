"""Verifier mode - checks if task is complete."""

from ...llm import Context
from ..schemas.mode import VerifyResult
from ...prompts import get_prompt
from .base_mode import BaseMode


class Verifier(BaseMode[VerifyResult]):
    """
    Verifier mode checks if the task is complete.

    Context includes:
    - Task description
    - Previous steps
    - Current page state
    - NO tool schemas (don't need them for verification)

    Returns VerifyResult with completion status and next mode suggestion.
    """

    async def _build_context(self) -> Context:
        """Build lightweight context for verification."""
        system = get_prompt("verifier_system")
        context = Context(system=system)

        # Add task description
        context.append(self.task_context.get_task_context())

        # Add step history
        context.append(self.task_context.get_steps_context())

        # Add current page state
        context.append(await self.llm_browser.get_page_context())

        return context

    async def execute(self) -> VerifyResult:
        """
        Execute verify mode.

        Checks if the current page state indicates task completion.

        Returns:
            VerifyResult with completion status and next mode
        """
        await self.throttler.wait()

        # Build context
        context = await self._build_context()
        self.throttler.update_timestamp()

        # Generate and validate response
        result = await self.validated_llm.generate_validated(
            context, validator=VerifyResult.model_validate
        )

        return result
