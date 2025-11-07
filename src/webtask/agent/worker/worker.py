"""Worker role - executes one subtask."""

from typing import Dict, Any, Optional
from ..tool import ToolRegistry
from ..tool_call import ProposedIteration, Iteration, ToolCall
from ..subtask import Subtask
from ..context import IterationContextBuilder, ToolContextBuilder, LLMBrowserContextBuilder
from ...llm import LLM, Context, Block
from ...llm_browser import LLMBrowser
from ...utils import parse_json


class Worker:
    """Worker executes browser actions for one subtask.

    Loops until mark_done tool is called, then returns control.
    """

    def __init__(
        self,
        llm: LLM,
        llm_browser: LLMBrowser,
        resources: Dict[str, str],
        logger=None,
    ):
        """Initialize Worker.

        Args:
            llm: LLM instance for generating actions
            llm_browser: Browser interface for executing actions
            resources: Task resources (e.g., file paths for upload)
            logger: Optional ExecutionLogger for tracking execution events
        """
        self._llm = llm
        self._llm_browser = llm_browser
        self._resources = resources
        self._logger = logger

        # Create and register worker tools
        self._tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all worker tools."""
        from .tools.navigate import NavigateTool
        from .tools.click import ClickTool
        from .tools.fill import FillTool
        from .tools.type import TypeTool
        from .tools.upload import UploadTool
        from .tools.wait import WaitTool

        # Browser action tools
        self._tool_registry.register(NavigateTool())
        self._tool_registry.register(ClickTool())
        self._tool_registry.register(FillTool())
        self._tool_registry.register(TypeTool())
        self._tool_registry.register(UploadTool())
        self._tool_registry.register(WaitTool())

    async def run(self, session: "WorkerSession") -> "WorkerSession":
        """Execute browser actions for the subtask.

        Worker no longer makes completion decisions - it just executes actions.
        Verifier will check if work succeeded.

        Args:
            session: WorkerSession with subtask and config, will be filled with iterations

        Returns:
            The same session, now filled with iterations
        """
        session.subtask.mark_in_progress()

        for i in range(session.max_iterations):
            if self._logger:
                self._logger.log_iteration_start("Worker", i + 1)

            # Build context (includes past iterations from this session)
            context = await self._build_context(session)

            # LLM proposes actions
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
                await self._tool_registry.execute_tool_call(
                    tool_call, llm_browser=self._llm_browser, resources=self._resources
                )
                iteration.add_tool_call(tool_call)
                if self._logger:
                    self._logger.log_tool_call("Worker", tool_call)

            # Add to session
            session.add_iteration(iteration)

            if self._logger:
                self._logger.log_iteration_complete("Worker", i + 1, iteration.message, len(tool_calls))

        # Worker completes all iterations - Verifier will decide if work succeeded
        return session

    async def _build_context(self, session: "WorkerSession") -> Context:
        """Build LLM context for worker.

        Includes:
        - System prompt
        - Subtask description (self-contained)
        - Past iterations from current session
        - Current page state
        - Available tools
        """
        from ...prompts import get_prompt

        system_prompt = get_prompt("worker_system")

        # Create context builders
        iteration_ctx = IterationContextBuilder(session.iterations)
        browser_ctx = LLMBrowserContextBuilder(self._llm_browser)
        tool_ctx = ToolContextBuilder(self._tool_registry)

        blocks = [
            Block(heading="Current Subtask", content=session.subtask.description),
            iteration_ctx.build_iterations_context(),
            await browser_ctx.build_page_context(),
            tool_ctx.build_tools_context(),
        ]

        return Context(system=system_prompt, user=blocks)
