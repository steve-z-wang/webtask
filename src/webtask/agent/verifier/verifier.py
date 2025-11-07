"""Verifier role - checks if subtask succeeded and if task is complete."""

from typing import Optional
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration, ToolCall
from ..context import IterationContextBuilder, ToolContextBuilder, LLMBrowserContextBuilder
from ...llm import LLM, Context, Block
from ...llm_browser import LLMBrowser
from ...utils import parse_json


class Verifier:
    """Verifier checks execution results and task completion.

    Receives worker session, verifies subtask success/failure, and checks task completion.
    """

    def __init__(
        self,
        llm: LLM,
        llm_browser: LLMBrowser,
        logger=None,
    ):
        """Initialize Verifier.

        Args:
            llm: LLM instance for verification decisions
            llm_browser: Browser interface for page observation
            logger: Optional ExecutionLogger for tracking verification events
        """
        self._llm = llm
        self._llm_browser = llm_browser
        self._logger = logger

        # Create and register verifier tools
        self._tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all verifier tools."""
        from .tools.mark_subtask_complete import MarkSubtaskCompleteTool
        from .tools.mark_subtask_failed import MarkSubtaskFailedTool
        from .tools.mark_task_complete import MarkTaskCompleteTool

        # Verification decision tools
        self._tool_registry.register(MarkSubtaskCompleteTool())
        self._tool_registry.register(MarkSubtaskFailedTool())
        self._tool_registry.register(MarkTaskCompleteTool())

    async def run(self, session: "VerifierSession") -> "VerifierSession":
        """Verify subtask and check task completion.

        Args:
            session: VerifierSession with subtask, worker results, and task context

        Returns:
            The same session, now filled with verification iterations and decisions
        """
        subtask_decision = None
        task_complete_decision = None

        for i in range(session.max_iterations):
            if self._logger:
                self._logger.log_iteration_start("Verifier", i + 1)

            # Build context (includes worker actions and current page state)
            context = await self._build_context(session)

            # LLM makes verification decisions
            response = await self._llm.generate(context, use_json=True)
            response_dict = parse_json(response)
            proposed = ProposedIteration.model_validate(response_dict)

            # Validate upfront
            tool_calls = self._tool_registry.validate_proposed_tools(
                proposed.tool_calls
            )

            # Create iteration (atomic pattern)
            iteration = Iteration.from_proposed(proposed)

            # Execute each tool call
            for tool_call in tool_calls:
                await self._tool_registry.execute_tool_call(tool_call)
                iteration.add_tool_call(tool_call)
                if self._logger:
                    self._logger.log_tool_call("Verifier", tool_call)

            # Add to session
            session.add_iteration(iteration)

            if self._logger:
                self._logger.log_iteration_complete("Verifier", i + 1, iteration.message, len(tool_calls))

            # Check for decisions
            subtask_decision = self._get_subtask_decision(tool_calls)
            task_complete_decision = self._get_task_complete_decision(tool_calls)

            if subtask_decision:
                # Update subtask status based on verification
                if subtask_decision.tool == "mark_subtask_complete":
                    session.subtask.mark_complete()
                elif subtask_decision.tool == "mark_subtask_failed":
                    session.subtask.mark_failed(subtask_decision.result)

            if task_complete_decision:
                # Update task completion flag
                session.task_complete = True
                session.task.mark_complete()
                break

            # If we have subtask decision, we're done (task may or may not be complete)
            if subtask_decision:
                break

        # Handle max iterations without decision
        if not subtask_decision:
            # Default to failure if verifier can't decide
            session.subtask.mark_failed("Verifier could not determine subtask status")

        return session

    def _get_subtask_decision(self, tool_calls) -> Optional["ToolCall"]:
        """Get subtask decision tool call if present and successful.

        Returns:
            The subtask decision ToolCall (mark_subtask_complete or mark_subtask_failed) if found, None otherwise
        """
        for tc in tool_calls:
            if tc.tool in ["mark_subtask_complete", "mark_subtask_failed"] and tc.success:
                return tc
        return None

    def _get_task_complete_decision(self, tool_calls) -> Optional["ToolCall"]:
        """Get task completion decision tool call if present and successful.

        Returns:
            The task completion ToolCall (mark_task_complete) if found, None otherwise
        """
        for tc in tool_calls:
            if tc.tool == "mark_task_complete" and tc.success:
                return tc
        return None

    async def _build_context(self, session: "VerifierSession") -> Context:
        """Build LLM context for verifier.

        Includes:
        - System prompt
        - Task goal (for task completion check)
        - Subtask description
        - Worker iterations (what worker did)
        - Current page state (to verify results)
        - Available tools
        """
        from ...prompts import get_prompt

        system_prompt = get_prompt("verifier_system")

        # Create context builders
        worker_ctx = IterationContextBuilder(session.worker_session.iterations)
        browser_ctx = LLMBrowserContextBuilder(self._llm_browser)
        tool_ctx = ToolContextBuilder(self._tool_registry)

        blocks = [
            Block(heading="Task Goal", content=session.task.description),
            Block(heading="Current Subtask", content=session.subtask.description),
            Block(heading="Worker Actions", content=worker_ctx.build_iterations_context().content),
            await browser_ctx.build_page_context(),
            tool_ctx.build_tools_context(),
        ]

        return Context(system=system_prompt, user=blocks)
