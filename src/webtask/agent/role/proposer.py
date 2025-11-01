"""Proposer - proposes next action and checks completion."""

from ...llm import LLM, Context, Block
from ...prompts import get_prompt
from ...utils import parse_json
from ..step import Action, ProposalResult
from ..step_history import StepHistory
from ...llm_browser import LLMBrowser
from ..tool import ToolRegistry


class Proposer:
    """Proposes the next action to take and determines if task is complete."""

    def __init__(
        self,
        llm: LLM,
        task: str,
        step_history: StepHistory,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
    ):
        self.llm = llm
        self.task = task
        self.step_history = step_history
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser

    async def _build_context(self) -> Context:
        system = get_prompt("proposer_system")
        context = Context(system=system)
        context.append(Block(f"Task:\n{self.task}"))
        context.append(self.step_history.to_context_block())
        context.append(self.tool_registry.to_context_block())
        context.append(await self.llm_browser.to_context_block())
        return context

    async def propose(self) -> ProposalResult:
        """Propose the next actions to take and determine if task is complete."""
        context = await self._build_context()
        response = await self.llm.generate(context)
        data = parse_json(response)

        # Parse completion status and message
        complete = data.get("complete")
        message = data.get("message")

        if complete is None or not message:
            raise ValueError(
                f"LLM response missing 'complete' or 'message' field.\n"
                f"LLM response: {response}"
            )

        # Parse actions
        actions_list = data.get("actions", [])
        actions = []

        for action_dict in actions_list:
            reason = action_dict.get("reason")
            tool_name = action_dict.get("tool")
            parameters = action_dict.get("parameters", {})

            if not reason or not tool_name:
                raise ValueError(
                    f"Action missing 'reason' or 'tool' field: {action_dict}"
                )

            if tool_name.lower() in ["none", "null", ""]:
                continue

            try:
                self.tool_registry.validate_tool_use(tool_name, parameters)
            except ValueError as e:
                available_tools = [t.name for t in self.tool_registry.get_all()]
                raise ValueError(
                    f"Invalid tool '{tool_name}': {e}\n"
                    f"Available tools: {', '.join(available_tools)}\n"
                    f"LLM response: {response}"
                )

            actions.append(
                Action(reason=reason, tool_name=tool_name, parameters=parameters)
            )

        return ProposalResult(complete=bool(complete), message=message, actions=actions)
