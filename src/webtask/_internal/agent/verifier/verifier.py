"""Verifier role - checks if subtask succeeded and if task is complete."""

from pathlib import Path
from typing import TYPE_CHECKING
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration
from webtask._internal.llm import Context, Block
from webtask._internal.llm import TypedLLM
from webtask._internal.config import Config
from ...prompts import build_verifier_prompt
from ...page_context import PageContextBuilder
from ..worker.worker_session import WorkerSession
from .verifier_session import VerifierSession
from .tools.complete_subtask import CompleteSubtaskTool
from .tools.request_reschedule import RequestRescheduleTool
from .tools.request_correction import RequestCorrectionTool
from ..worker.tools.wait import WaitTool

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser


class Verifier:
    """Verifier role - checks if subtask succeeded and if task is complete."""

    def __init__(self, typed_llm: TypedLLM, agent_browser: "AgentBrowser"):
        self._llm = typed_llm
        self._agent_browser = agent_browser
        self._tool_registry = ToolRegistry()
        self._tool_registry.register(CompleteSubtaskTool())
        self._tool_registry.register(RequestRescheduleTool())
        self._tool_registry.register(RequestCorrectionTool())
        self._tool_registry.register(WaitTool())

    def _save_debug_context(self, filename: str, context):
        """Save context (text + images) for debugging. Returns dict with paths."""
        debug_dir = Path(Config().get_debug_dir())
        debug_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Save text context
        text_path = debug_dir / f"{filename}.txt"
        with open(text_path, "w") as f:
            f.write(context.to_text())
        paths["text"] = str(text_path)

        # Extract and save images from context
        images = context.get_images()
        for i, image in enumerate(images):
            img_path = debug_dir / f"{filename}_img_{i}.png"
            image.save(str(img_path))
            paths[f"image_{i}"] = str(img_path)

        return paths

    async def _build_page_context(self) -> Block:
        page = self._agent_browser.get_current_page()

        # Wait for page to be idle after worker actions (max 5s)
        await page.wait_for_idle(timeout=5000)

        block, _ = await PageContextBuilder.build(
            page=page,
            include_element_ids=False,
            with_bounding_boxes=False,
            full_page_screenshot=False,
        )
        return block

    def _format_worker_actions(self, worker_iterations: list) -> Block:
        """Format worker actions for verifier context.

        Only shows the actions taken, not internal reasoning.
        """
        if not worker_iterations:
            return Block(heading="Worker Actions", content="No worker actions yet.")

        content = ""
        for iteration in worker_iterations:
            content += f"\n**Iteration {iteration.iteration_number}**\n"
            for tc in iteration.tool_calls:
                status = "[SUCCESS]" if tc.success else "[FAILED]"
                content += f"  {status} {tc.description}\n"
                if not tc.success and tc.error:
                    content += f"     Error: {tc.error}\n"

        return Block(heading="Worker Actions", content=content.strip())

    def _format_correction_history(self, subtask_execution) -> Block:
        """Format correction history showing Worker/Verifier attempts."""
        if not subtask_execution or not subtask_execution.history:
            return Block(
                heading="Correction History",
                content="No previous attempts for this subtask.",
            )

        correction_count = subtask_execution.get_correction_count()
        content = f"Correction attempts so far: {correction_count}/3\n"

        for session in subtask_execution.history:
            if isinstance(session, WorkerSession):
                content += f"\n**Worker Session {session.session_number}**\n"
                for iteration in session.iterations:
                    for tc in iteration.tool_calls:
                        status = "[SUCCESS]" if tc.success else "[FAILED]"
                        content += f"  {status} {tc.description}\n"
                        if not tc.success and tc.error:
                            content += f"     Error: {tc.error}\n"
            else:
                # VerifierSession
                content += f"\n**Verifier Session {session.session_number}**\n"
                if session.subtask_decision:
                    content += f"  Decision: {session.subtask_decision.tool}\n"
                    feedback = session.subtask_decision.parameters.get("feedback", "")
                    if feedback:
                        content += f"  Feedback: {feedback}\n"

        return Block(heading="Correction History", content=content.strip())

    async def _build_context(
        self,
        task_description: str,
        subtask_description: str,
        worker_iterations: list = None,
        subtask_execution=None,
    ) -> Context:
        page_context = await self._build_page_context()
        context = (
            Context()
            .with_system(build_verifier_prompt())
            .with_block(Block(heading="Task Goal", content=task_description))
            .with_block(Block(heading="Current Subtask", content=subtask_description))
        )

        # Use subtask_execution if available, otherwise fall back to worker_iterations
        if subtask_execution:
            context = context.with_block(
                self._format_correction_history(subtask_execution)
            )
        elif worker_iterations:
            context = context.with_block(self._format_worker_actions(worker_iterations))

        context = context.with_block(self._tool_registry.get_context())
        context = context.with_block(page_context)

        return context

    async def run(
        self,
        task_description: str,
        subtask_description: str,
        worker_session: WorkerSession = None,
        max_iterations: int = 3,
        session_number: int = 1,
        subtask_index: int = 0,
        subtask_execution=None,
    ) -> VerifierSession:
        subtask_decision = None
        iterations = []

        for i in range(max_iterations):
            iteration_number = i + 1  # 1-indexed for display/output
            # Use subtask_execution if available, otherwise fall back to worker_session
            if subtask_execution:
                context = await self._build_context(
                    task_description,
                    subtask_description,
                    subtask_execution=subtask_execution,
                )
            else:
                context = await self._build_context(
                    task_description,
                    subtask_description,
                    worker_iterations=(
                        worker_session.iterations if worker_session else []
                    ),
                )

            # Save debug info if enabled
            if Config().is_debug_enabled():
                self._save_debug_context(
                    f"subtask_{subtask_index}_session_{session_number}_verifier_iter_{iteration_number}",
                    context,
                )

            proposed = await self._llm.generate(context, ProposedIteration)
            tool_calls = self._tool_registry.validate_proposed_tools(
                proposed.tool_calls
            )

            for tool_call in tool_calls:
                await self._tool_registry.execute_tool_call(tool_call)

            iteration = Iteration(
                iteration_number=iteration_number,
                observation=proposed.observation,
                thinking=proposed.thinking,
                tool_calls=tool_calls,
            )
            iterations.append(iteration)

            for tc in tool_calls:
                if (
                    tc.tool
                    in ["complete_subtask", "request_reschedule", "request_correction"]
                    and tc.success
                ):
                    subtask_decision = tc

            if subtask_decision:
                break

        return VerifierSession(
            session_number=session_number,
            task_description=task_description,
            subtask_description=subtask_description,
            worker_session=worker_session,
            max_iterations=max_iterations,
            iterations=iterations,
            subtask_decision=subtask_decision,
        )
