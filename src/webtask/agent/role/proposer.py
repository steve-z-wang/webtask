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
    """
    Proposes the next action to take based on context.

    Uses LLM to analyze task, history, and current page state to propose actions.
    """

    def __init__(
        self,
        llm: LLM,
        task: str,
        step_history: StepHistory,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
    ):
        """
        Initialize proposer.

        Args:
            llm: LLM instance for generating proposals
            task: Task description string
            step_history: StepHistory instance
            tool_registry: ToolRegistry instance
            llm_browser: LLMBrowser instance
        """
        self.llm = llm
        self.task = task
        self.step_history = step_history
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser

    async def _build_context(self) -> Context:
        """
        Build context for proposer.

        Returns:
            Context with system and user prompts
        """
        # System prompt from library
        system = get_prompt("proposer_system")

        # Build user prompt
        context = Context(system=system)

        # Task
        context.append(Block(f"Task:\n{self.task}"))

        # Step history
        context.append(self.step_history.to_context_block())

        # Tools
        context.append(self.tool_registry.to_context_block())

        # Page
        context.append(await self.llm_browser.to_context_block())

        return context

    async def propose(self) -> List[Action]:
        """
        Propose the next actions to take.

        Returns:
            List of Actions to execute

        Raises:
            Exception: If LLM fails to propose valid actions
        """
        # Build context
        context = await self._build_context()

        # Call LLM
        response = await self.llm.generate(context)

        # Parse JSON response
        action_data = parse_json(response)

        # Extract actions array
        actions_list = action_data.get("actions", [])

        # If no actions (task might be complete), return empty list
        # Verifier will determine if task is actually complete
        if not actions_list:
            return []

        # Parse each action
        actions = []
        for action_dict in actions_list:
            reason = action_dict.get("reason")
            tool_name = action_dict.get("tool")
            parameters = action_dict.get("parameters", {})

            if not reason or not tool_name:
                raise ValueError(
                    f"Action missing 'reason' or 'tool' field: {action_dict}"
                )

            # Skip invalid tool names like "none"
            if tool_name.lower() in ["none", "null", ""]:
                # LLM indicated no action should be taken
                continue

            # Validate tool and parameters
            try:
                self.tool_registry.validate_tool_use(tool_name, parameters)
            except ValueError as e:
                # Provide better error message with available tools
                available_tools = [t.name for t in self.tool_registry.get_all()]
                raise ValueError(
                    f"Invalid tool '{tool_name}': {e}\n"
                    f"Available tools: {', '.join(available_tools)}\n"
                    f"LLM response: {response}"
                )

            # Create Action
            actions.append(
                Action(reason=reason, tool_name=tool_name, parameters=parameters)
            )

        return actions
