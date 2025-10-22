"""Verifier role - verifies task completion."""

from ...llm import LLM, Context, Block
from ...prompts import get_prompt
from ...utils import parse_json
from ..step import Action, ExecutionResult, VerificationResult
from ..step_history import StepHistory
from ...llm_browser import LLMBrowser


class Verifier:
    """
    Verifies whether the task has been completed.

    Uses LLM to analyze task, step history, current action/result, and page state.
    """

    def __init__(
        self,
        llm: LLM,
        task: str,
        step_history: StepHistory,
        llm_browser: LLMBrowser,
    ):
        """
        Initialize verifier.

        Args:
            llm: LLM instance for verification
            task: Task description string
            step_history: StepHistory instance
            llm_browser: LLMBrowser instance
        """
        self.llm = llm
        self.task = task
        self.step_history = step_history
        self.llm_browser = llm_browser

    async def _build_context(
        self, action: Action, execution_result: ExecutionResult
    ) -> Context:
        """
        Build context for verifier.

        Args:
            action: Current action that was executed
            execution_result: Result of current action execution

        Returns:
            Context with system and user prompts
        """
        # System prompt from library
        system = get_prompt("verifier_system")

        # Build user prompt
        context = Context(system=system)

        # Task
        context.append(f"Task: {self.task}")

        # Step history (completed steps)
        context.append(self.step_history.to_context_block())

        # Current action and result
        current = Block("Current Action:")
        current.append(f"Action: {action.tool_name}")
        current.append(f"Reason: {action.reason}")
        current.append(f"Parameters: {action.parameters}")
        current.append(f"Execution: {'Success' if execution_result.success else 'Failed'}")
        if execution_result.error:
            current.append(f"Error: {execution_result.error}")
        context.append(current)

        # Page
        context.append(await self.llm_browser.to_context_block())

        return context

    async def verify(
        self, action: Action, execution_result: ExecutionResult
    ) -> VerificationResult:
        """
        Verify if the task is complete.

        Args:
            action: Current action that was executed
            execution_result: Result of current action execution

        Returns:
            VerificationResult with completion status and message

        Raises:
            Exception: If LLM fails to provide valid verification
        """
        # Build context
        context = await self._build_context(action, execution_result)

        # Call LLM
        response = self.llm.generate(context)

        # Parse JSON response
        verification_data = parse_json(response)

        # Extract fields
        complete = verification_data.get("complete")
        message = verification_data.get("message")

        if complete is None or not message:
            raise ValueError("LLM response missing 'complete' or 'message' field")

        # Create and return VerificationResult
        return VerificationResult(complete=bool(complete), message=message)
