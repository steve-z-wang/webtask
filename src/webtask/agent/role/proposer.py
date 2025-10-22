"""Proposer - proposes next action based on context."""

from ...llm import LLM, Context
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
        context.append(f"Task: {self.task}")

        # Step history
        context.append(self.step_history.to_context_block())

        # Tools
        context.append(self.tool_registry.to_context_block())

        # Page
        context.append(await self.llm_browser.to_context_block())

        return context

    async def propose(self) -> Action:
        """
        Propose the next action to take.

        Returns:
            Action to execute

        Raises:
            Exception: If LLM fails to propose a valid action
        """
        # Build context
        context = await self._build_context()

        # Call LLM
        response = self.llm.generate(context)

        # Parse JSON response
        action_data = parse_json(response)

        # Extract fields
        reason = action_data.get("reason")
        tool_name = action_data.get("tool")
        parameters = action_data.get("parameters", {})

        if not reason or not tool_name:
            raise ValueError("LLM response missing 'reason' or 'tool' field")

        # Validate tool and parameters
        self.tool_registry.validate_tool_use(tool_name, parameters)

        # Create and return Action
        return Action(reason=reason, tool_name=tool_name, parameters=parameters)
