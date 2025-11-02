"""Proposer - proposes next action and checks completion."""

from ...llm import LLM, Context, Block
from ...prompts import get_prompt
from ...utils import parse_json
from ..step import Action, ProposalResult
from ..task_context import TaskContext
from ...llm_browser import LLMBrowser
from ..tool import ToolRegistry


class Proposer:
    """Proposes the next action to take and determines if task is complete."""

    def __init__(
        self,
        llm: LLM,
        task_context: TaskContext,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
    ):
        self.llm = llm
        self.task_context = task_context
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser

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

    async def propose(self) -> ProposalResult:
        """Propose the next actions to take and determine if task is complete."""
        context = await self._build_context()
        response = await self.llm.generate(context, json_mode=True)
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

        # Validate logical consistency: cannot be complete AND have actions
        if complete and actions:
            raise ValueError(
                f"Invalid LLM response: cannot set complete=True AND propose actions.\n"
                f"If task is complete, actions list must be empty.\n"
                f"LLM response: {response}"
            )

        return ProposalResult(complete=bool(complete), message=message, actions=actions)
