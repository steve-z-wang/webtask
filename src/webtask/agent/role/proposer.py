"""Proposer - proposes next action based on context."""

from typing import List
from ...llm import LLM, Context, Block
from ...prompts import get_prompt
from ...utils import parse_json
from ..step import Action
from ..step_history import StepHistory
from ...llm_browser import LLMBrowser
from ..tool import ToolRegistry


class Proposer:
    """Proposes the next action to take based on context."""

    def __init__(
        self,
        llm: LLM,
        task: str,
        step_history: StepHistory,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
        use_screenshot: bool = False,
    ):
        self.llm = llm
        self.task = task
        self.step_history = step_history
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser
        self.use_screenshot = use_screenshot

    async def _build_context(self) -> Context:
        system = get_prompt("proposer_system")
        context = Context(system=system)
        context.append(Block(f"Task:\n{self.task}"))
        context.append(self.step_history.to_context_block())
        context.append(self.tool_registry.to_context_block())
        context.append(await self.llm_browser.to_context_block(use_screenshot=self.use_screenshot))
        return context

    async def propose(self) -> List[Action]:
        """Propose the next actions to take."""
        context = await self._build_context()
        response = await self.llm.generate(context)
        action_data = parse_json(response)
        actions_list = action_data.get("actions", [])

        if not actions_list:
            return []

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

        return actions
