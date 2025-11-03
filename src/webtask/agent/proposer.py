"""Proposer - proposes next action and checks completion."""

from ..llm import LLM, Context
from ..prompts import get_prompt
from .schemas import Proposal
from .task import Task
from ..llm_browser import LLMBrowser
from .tool import ToolRegistry
from .throttler import Throttler
from ..utils.json_parser import parse_json


class Proposer:
    """Proposes the next action to take and determines if task is complete."""

    def __init__(
        self,
        llm: LLM,
        task_context: Task,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        self.llm = llm
        self.task_context = task_context
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser
        self.throttler = throttler

    async def _build_context(self) -> Context:
        system = get_prompt("proposer_system")
        context = Context(system=system)

        # Add task (TaskContext owns formatting)
        context.append(self.task_context.get_task_context())

        # Add resources if available (TaskContext owns formatting)
        resources_context = self.task_context.get_resources_context()
        if resources_context:
            context.append(resources_context)

        # Add step history (TaskContext owns formatting)
        context.append(self.task_context.get_steps_context())

        # Add available tools
        context.append(self.tool_registry.get_tools_context())

        # Add current page context (text + optional screenshots)
        context.append(await self.llm_browser.get_page_context())

        return context

    async def propose(self) -> Proposal:
        """Propose the next actions to take and determine if task is complete."""
        context = await self._build_context()

        # Throttle before LLM call
        await self.throttler.wait_if_needed()
        response = await self.llm.generate(context, use_json=True)

        # Clean JSON (remove markdown fences if present) and parse into Pydantic model
        cleaned_json_dict = parse_json(response)
        proposal = Proposal.model_validate(cleaned_json_dict)

        # Validate logical consistency: cannot be complete AND have actions
        if proposal.complete and proposal.actions:
            raise ValueError(
                "Invalid LLM response: cannot set complete=True AND propose actions.\n"
                "If task is complete, actions list must be empty."
            )

        return proposal
