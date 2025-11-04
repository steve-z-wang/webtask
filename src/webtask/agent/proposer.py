"""Proposer - proposes next action and checks completion."""

from pydantic import TypeAdapter
from ..llm import LLM, Context
from ..prompts import get_prompt
from .schemas import ProposalResponse
from .task import Task
from ..llm_browser import LLMBrowser
from .tool import ToolRegistry
from .throttler import Throttler
from ..utils.json_parser import parse_json

# TypeAdapter for validating discriminated union
_proposal_adapter = TypeAdapter(ProposalResponse)


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

        context.append(self.task_context.get_task_context())

        resources_context = self.task_context.get_resources_context()
        if resources_context:
            context.append(resources_context)

        context.append(self.tool_registry.get_tools_context())

        context.append(self.task_context.get_steps_context())

        context.append(await self.llm_browser.get_page_context())

        return context

    async def propose(self) -> ProposalResponse:
        """Propose the next actions to take and determine if task is complete."""
        await self.throttler.wait()

        # Throttle LLM call (update timestamp before since LLM has no side effects)
        context = await self._build_context()
        self.throttler.update_timestamp()

        response = await self.llm.generate(context, use_json=True)

        # Clean JSON (remove markdown fences if present) and parse into Pydantic model
        # Pydantic will automatically return FinalProposal or ActionProposal
        # based on the 'complete' field (discriminated union)
        cleaned_json_dict = parse_json(response)
        proposal = _proposal_adapter.validate_python(cleaned_json_dict)

        return proposal
