"""Proposer - proposes next action based on context."""

import json
from ....llm import LLM, Context
from ...action import Action, ActionHistory
from ...llm_browser import LLMBrowser
from ...tool import ToolRegistry


class Proposer:
    """
    Proposes the next action to take based on context.

    Uses LLM to analyze task, history, and current page state to propose actions.
    """

    def __init__(
        self,
        llm: LLM,
        task: str,
        action_history: ActionHistory,
        tool_registry: ToolRegistry,
        llm_browser: LLMBrowser,
    ):
        """
        Initialize proposer.

        Args:
            llm: LLM instance for generating proposals
            task: Task description string
            action_history: ActionHistory instance
            tool_registry: ToolRegistry instance
            llm_browser: LLMBrowser instance
        """
        self.llm = llm
        self.task = task
        self.action_history = action_history
        self.tool_registry = tool_registry
        self.llm_browser = llm_browser

    async def _build_context(self) -> Context:
        """
        Build context for proposer.

        Returns:
            Context with system and user prompts
        """
        # System prompt
        system = """You are a web automation agent. Your task is to propose the next action to take.

You will receive:
- The task to accomplish
- Action history (what has been done so far)
- Available tools and their schemas
- Current page state with element IDs

You must respond with a JSON object containing:
{
  "reason": "Brief explanation of why you're taking this action",
  "tool": "tool_name",
  "parameters": {
    "param1": "value1",
    ...
  }
}

Important:
- Use element IDs from the page context (e.g., "button-0", "input-1")
- Only use tools that are available
- Provide clear reasoning for your actions
"""

        # Build user prompt
        context = Context(system=system)

        # Task
        context.append(f"Task: {self.task}")

        # Action history
        if not self.action_history._actions:
            context.append("No actions executed yet.")
        else:
            history_lines = ["Action History:"]
            for i, action in enumerate(self.action_history._actions, 1):
                history_lines.append(f"{i}. {action.tool_name}")
                history_lines.append(f"   Reason: {action.reason}")
                history_lines.append(f"   Parameters: {action.parameters}")
            context.append("\n".join(history_lines))

        # Tools
        import json as json_lib
        schemas = [tool.to_schema() for tool in self.tool_registry.get_all()]
        context.append(json_lib.dumps(schemas, indent=2))

        # Page
        context.append(await self.llm_browser.get_context())

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
        try:
            action_data = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

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
