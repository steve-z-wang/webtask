"""Scheduler - plans work at high level without page access."""

from typing import TYPE_CHECKING, Optional
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration, ToolCall
from ...llm import Context, LLM, Block
from ...utils import parse_json

if TYPE_CHECKING:
    from ..task import TaskExecution


class Scheduler:
    """
    Scheduler role - plans work at high level.

    Context:
    - Task description (no page access)
    - Execution history
    - Available resources
    - Current subtask backlog

    Tools:
    - set_subtasks, add_subtask, insert_subtask, delete_subtask, update_subtask
    - start_work (transition)

    Loops until start_work is called.
    """

    def __init__(self, llm: LLM, logger=None):
        """
        Initialize scheduler.

        Args:
            llm: LLM instance for generating responses
            logger: Optional ExecutionLogger for tracking execution events
        """
        self._llm = llm
        self._logger = logger

        # Create and register scheduler tools
        self._tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register scheduler tools."""
        from .tools import (
            AddSubtaskTool,
            CancelSubtaskTool,
            StartWorkTool,
        )

        self._tool_registry.register(AddSubtaskTool())
        self._tool_registry.register(CancelSubtaskTool())
        self._tool_registry.register(StartWorkTool())

    async def _build_context(self, session: "SchedulerSession") -> Context:
        """
        Build context for scheduler (no page access).

        Includes:
        - Task description
        - Subtask queue with status
        """
        from ...prompts import get_prompt
        from ..context import SubtaskQueueContextBuilder

        system = get_prompt("scheduler_system")

        queue_builder = SubtaskQueueContextBuilder(session.task.subtask_queue)

        blocks = [
            Block(heading="Task", content=session.task.description),
            queue_builder.build_queue_context(),
        ]

        return Context(system=system, user=blocks)

    async def run(self, session: "SchedulerSession") -> "SchedulerSession":
        """
        Run scheduler until start_work is called.

        Flow:
        1. Build context (no page)
        2. Loop:
           - Call LLM for proposed iteration
           - Validate and execute tool calls
           - Check for start_work transition
        3. Return SchedulerSession when start_work called

        Args:
            session: SchedulerSession with config, will be filled with iterations

        Returns:
            The same session, now filled with iterations and decision
        """
        start_work_call = None

        for i in range(session.max_iterations):
            if self._logger:
                self._logger.log_iteration_start("Scheduler", i + 1)

            # Build context (includes past iterations from this session)
            context = await self._build_context(session)

            # Generate proposed iteration
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
                await self._tool_registry.execute_tool_call(tool_call, task=session.task)
                iteration.add_tool_call(tool_call)
                if self._logger:
                    self._logger.log_tool_call("Scheduler", tool_call)

            # Add to session
            session.add_iteration(iteration)

            if self._logger:
                self._logger.log_iteration_complete("Scheduler", i + 1, iteration.message, len(tool_calls))

            # Check for start_work transition
            start_work_call = self._get_start_work(tool_calls)
            if start_work_call:
                break

        return session

    def _get_start_work(self, tool_calls) -> Optional["ToolCall"]:
        """Get start_work tool call if present and successful.

        Returns:
            The start_work ToolCall if found, None otherwise
        """
        for tc in tool_calls:
            if tc.tool == "start_work" and tc.success:
                return tc
        return None
