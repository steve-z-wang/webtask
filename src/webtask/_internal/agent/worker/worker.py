"""Worker role - executes one subtask."""

from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration
from webtask._internal.llm import Context, Block
from webtask._internal.llm import TypedLLM
from webtask._internal.config import Config
from ...prompts.worker_prompt import build_worker_prompt
from webtask._internal.utils.wait import wait
from .worker_browser import WorkerBrowser
from .worker_session import WorkerSession
from .tools.navigate import NavigateTool
from .tools.click import ClickTool
from .tools.fill import FillTool
from .tools.type import TypeTool
from .tools.upload import UploadTool
from .tools.wait import WaitTool
from .tools.mark_done_working import MarkDoneWorkingTool

if TYPE_CHECKING:
    from ..agent_browser import AgentBrowser


class Worker:
    """Worker role - executes one subtask."""

    # Small delay after each action to prevent race conditions
    ACTION_DELAY = 0.1

    def __init__(self, typed_llm: TypedLLM, agent_browser: "AgentBrowser"):
        self._llm = typed_llm
        self.worker_browser = WorkerBrowser(agent_browser)
        self.resources: Dict[str, Any] = {}
        self._tool_registry = ToolRegistry()
        self._tool_registry.register(NavigateTool())
        self._tool_registry.register(ClickTool())
        self._tool_registry.register(FillTool())
        self._tool_registry.register(TypeTool())
        self._tool_registry.register(UploadTool())
        self._tool_registry.register(WaitTool())
        self._tool_registry.register(MarkDoneWorkingTool())

    def set_resources(self, resources: Dict[str, str]) -> None:
        self.resources = resources

    def _save_debug_context(self, filename: str, context: Context):
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

    def _format_own_iterations(self, iterations: list) -> Block:
        """Format worker's own iterations for context (shows full observation/thinking).

        Since this is the worker's own history within the same session,
        it shows full details to help maintain continuity.
        """
        if not iterations:
            return Block(
                heading="Current Session Iterations",
                content="No iterations yet in this session.",
            )

        content = ""
        for iteration in iterations:
            content += f"\n**Iteration {iteration.iteration_number}**\n"
            content += f"Observation: {iteration.observation}\n"
            content += f"Thinking: {iteration.thinking}\n"
            content += f"Actions: {len(iteration.tool_calls)}\n"
            for tc in iteration.tool_calls:
                status = "[SUCCESS]" if tc.success else "[FAILED]"
                content += f"  {status} {tc.description}\n"
                if not tc.success and tc.error:
                    content += f"     Error: {tc.error}\n"

        return Block(heading="Current Session Iterations", content=content.strip())

    def _format_subtask_history(self, subtask_execution) -> Block:
        """Format complete Worker/Verifier history for context."""
        if not subtask_execution or not subtask_execution.history:
            return Block(
                heading="Previous Attempts",
                content="No previous attempts for this subtask.",
            )

        from .worker_session import WorkerSession
        from ..verifier.verifier_session import VerifierSession

        content = ""
        for session in subtask_execution.history:
            if isinstance(session, WorkerSession):
                content += f"\n**Worker Session {session.session_number}**\n"
                for iteration in session.iterations:
                    for tc in iteration.tool_calls:
                        status = "[SUCCESS]" if tc.success else "[FAILED]"
                        content += f"  {status} {tc.description}\n"
                        if not tc.success and tc.error:
                            content += f"     Error: {tc.error}\n"
            elif isinstance(session, VerifierSession):
                content += f"\n**Verifier Session {session.session_number}**\n"
                if session.subtask_decision:
                    content += f"  Decision: {session.subtask_decision.tool}\n"
                    feedback = session.subtask_decision.parameters.get("feedback", "")
                    if feedback:
                        content += f"  Feedback: {feedback}\n"

        return Block(heading="Previous Attempts", content=content.strip())

    async def _build_context(
        self, subtask_description: str, iterations: list, subtask_execution=None
    ) -> Context:
        page_context = await self.worker_browser.get_context(
            include_element_ids=True,
            with_bounding_boxes=True,
        )
        context = (
            Context()
            .with_system(build_worker_prompt())
            .with_block(Block(heading="Current Subtask", content=subtask_description))
            .with_block(self._tool_registry.get_context())
        )

        # Add previous attempts if available
        if subtask_execution:
            context = context.with_block(
                self._format_subtask_history(subtask_execution)
            )

        context = context.with_block(self._format_own_iterations(iterations))
        context = context.with_block(page_context)

        return context

    async def run(
        self,
        subtask_description: str,
        max_iterations: int = 10,
        session_number: int = 1,
        subtask_index: int = 0,
        subtask_execution=None,
    ) -> WorkerSession:
        iterations = []

        for i in range(max_iterations):
            iteration_number = i + 1  # 1-indexed for display/output
            context = await self._build_context(
                subtask_description, iterations, subtask_execution
            )

            # Save debug info if enabled
            if Config().is_debug_enabled():
                self._save_debug_context(
                    f"subtask_{subtask_index}_session_{session_number}_worker_iter_{iteration_number}",
                    context,
                )

            proposed = await self._llm.generate(context, ProposedIteration)
            tool_calls = self._tool_registry.validate_proposed_tools(
                proposed.tool_calls
            )

            for tool_call in tool_calls:
                await self._tool_registry.execute_tool_call(
                    tool_call,
                    worker_browser=self.worker_browser,
                    resources=self.resources,
                )
                await wait(self.ACTION_DELAY)

            iteration = Iteration(
                iteration_number=iteration_number,
                observation=proposed.observation,
                thinking=proposed.thinking,
                tool_calls=tool_calls,
            )
            iterations.append(iteration)

            if any(tc.tool == "mark_done_working" and tc.success for tc in tool_calls):
                break

        return WorkerSession(
            session_number=session_number,
            subtask_description=subtask_description,
            max_iterations=max_iterations,
            iterations=iterations,
        )
