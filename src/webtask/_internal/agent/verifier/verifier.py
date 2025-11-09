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
from .tools.mark_subtask_complete import MarkSubtaskCompleteTool
from .tools.mark_subtask_failed import MarkSubtaskFailedTool
from ..worker.tools.wait import WaitTool

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser


class Verifier:
    """Verifier role - checks if subtask succeeded and if task is complete."""

    def __init__(self, typed_llm: TypedLLM, agent_browser: "AgentBrowser"):
        self._llm = typed_llm
        self._agent_browser = agent_browser
        self._tool_registry = ToolRegistry()
        self._tool_registry.register(MarkSubtaskCompleteTool())
        self._tool_registry.register(MarkSubtaskFailedTool())
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

    async def _build_context(
        self,
        task_description: str,
        subtask_description: str,
        worker_iterations: list,
    ) -> Context:
        page_context = await self._build_page_context()
        return (
            Context()
            .with_system(build_verifier_prompt())
            .with_block(Block(heading="Task Goal", content=task_description))
            .with_block(Block(heading="Current Subtask", content=subtask_description))
            .with_block(self._format_worker_actions(worker_iterations))
            .with_block(self._tool_registry.get_context())
            .with_block(page_context)
        )

    async def run(
        self,
        task_description: str,
        subtask_description: str,
        worker_session: WorkerSession,
        max_iterations: int = 3,
        session_id: int = 0,
    ) -> VerifierSession:
        session_number = session_id  # Already 1-indexed from task_executor
        subtask_decision = None
        iterations = []

        for i in range(max_iterations):
            iteration_number = i + 1  # 1-indexed for display/output
            context = await self._build_context(
                task_description, subtask_description, worker_session.iterations
            )

            # Save debug info if enabled
            if Config().is_debug_enabled():
                self._save_debug_context(
                    f"session_{session_number}_verifier_iter_{iteration_number}",
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
                    tc.tool in ["mark_subtask_complete", "mark_subtask_failed"]
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
