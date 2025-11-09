"""Manager - manages task and delegates subtasks."""

from pathlib import Path
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration
from ..subtask_queue import SubtaskQueue
from webtask._internal.llm import Context, Block
from webtask._internal.llm import TypedLLM
from webtask._internal.config import Config
from ...prompts import build_manager_prompt
from .manager_session import ManagerSession
from .tools import (
    AddSubtaskTool,
    CancelPendingSubtasksTool,
    StartSubtaskTool,
    CompleteTaskTool,
    AbortTaskTool,
)


class Manager:
    """Manager role - task-level oversight and subtask delegation."""

    def __init__(self, typed_llm: TypedLLM):
        self._llm = typed_llm
        self._tool_registry = ToolRegistry()
        self._tool_registry.register(AddSubtaskTool())
        self._tool_registry.register(CancelPendingSubtasksTool())
        self._tool_registry.register(StartSubtaskTool())
        self._tool_registry.register(CompleteTaskTool())
        self._tool_registry.register(AbortTaskTool())

    def _save_debug_context(self, filename: str, context: Context):
        """Save context (text only, no images in manager) for debugging."""
        debug_dir = Path(Config().get_debug_dir())
        debug_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Save text context
        text_path = debug_dir / f"{filename}.txt"
        with open(text_path, "w") as f:
            f.write(context.to_text())
        paths["text"] = str(text_path)

        return paths

    def _format_verifier_decision(self, verifier_session) -> Block:
        """Format verifier decision for manager context.

        Only shows the final decision (tool call) with details, not internal reasoning.
        """
        if not verifier_session.iterations:
            return Block(
                heading="Last Verifier Decision", content="No verifier decision yet."
            )

        # Get the last iteration's tool calls (should be the decision)
        last_iteration = verifier_session.iterations[-1]

        if not last_iteration.tool_calls:
            return Block(heading="Last Verifier Decision", content="No decision made.")

        content = ""
        for tc in last_iteration.tool_calls:
            status = "[SUCCESS]" if tc.success else "[FAILED]"
            content += f"{status} {tc.description}\n"

            # Show details from tool parameters
            details = tc.parameters.get("details") or tc.parameters.get(
                "failure_reason"
            )
            if details:
                label = (
                    "Failure reason"
                    if tc.parameters.get("failure_reason")
                    else "Details"
                )
                content += f"   {label}: {details}\n"
            if not tc.success and tc.error:
                content += f"   Error: {tc.error}\n"

        return Block(heading="Last Verifier Decision", content=content.strip())

    async def _build_context(
        self,
        task_description: str,
        subtask_queue: SubtaskQueue,
        iterations: list,
        last_verifier_session=None,
    ) -> Context:
        context = (
            Context()
            .with_system(build_manager_prompt())
            .with_block(Block(heading="Task Goal", content=task_description))
            .with_block(self._tool_registry.get_context())
            .with_block(subtask_queue.get_context())
        )

        # Add last verifier decision if available
        if last_verifier_session:
            verifier_decision = self._format_verifier_decision(last_verifier_session)
            context = context.with_block(verifier_decision)

        return context

    async def run(
        self,
        task_description: str,
        subtask_queue: SubtaskQueue,
        max_iterations: int = 10,
        session_id: int = 0,
        last_verifier_session=None,
    ) -> ManagerSession:
        session_number = session_id  # Already 1-indexed from task_executor
        iterations = []

        for i in range(max_iterations):
            iteration_number = i + 1  # 1-indexed for display/output
            context = await self._build_context(
                task_description, subtask_queue, iterations, last_verifier_session
            )

            # Save debug info if enabled
            if Config().is_debug_enabled():
                self._save_debug_context(
                    f"manager_session_{session_number}_iter_{iteration_number}", context
                )

            proposed = await self._llm.generate(context, ProposedIteration)
            tool_calls = self._tool_registry.validate_proposed_tools(
                proposed.tool_calls
            )

            for tool_call in tool_calls:
                await self._tool_registry.execute_tool_call(
                    tool_call, subtask_queue=subtask_queue
                )

            iteration = Iteration(
                iteration_number=iteration_number,
                observation=proposed.observation,
                thinking=proposed.thinking,
                tool_calls=tool_calls,
            )
            iterations.append(iteration)

            # Break when start_subtask is called (signals ready to execute)
            # or when complete_task/abort_task is called
            if any(
                tc.tool in ["start_subtask", "complete_task", "abort_task"]
                and tc.success
                for tc in tool_calls
            ):
                break

        return ManagerSession(
            session_number=session_number,
            task_description=task_description,
            max_iterations=max_iterations,
            iterations=iterations,
        )
