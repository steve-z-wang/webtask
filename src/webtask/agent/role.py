"""Base class for agent roles."""

import json
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, ValidationError
from ..llm import LLM, Block
from ..llm_browser import LLMBrowser
from ..utils.throttler import Throttler
from ..utils.json_parser import parse_json
from .schemas.proposal import Proposal, Action

if TYPE_CHECKING:
    from ..llm import Context
    from .task import Task


class ActionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    error: Optional[str] = None


class BaseRole(ABC):
    """
    Base class for agent roles (Verifier, Proposer, Planner, etc.).

    Each role has two responsibilities:
    1. Propose actions (thinking) - calls LLM to decide what to do
    2. Execute actions (doing) - runs the proposed actions using its tool registry

    Each role has:
    - Different context building (what info to send to LLM)
    - Different prompts (how to instruct LLM)
    - Different tool registry (what actions they can propose/execute)

    All roles share:
    - LLM for generating responses (with validation and retry in BaseRole)
    - Task context for task state
    - LLMBrowser for page access
    - Throttler for rate limiting
    """

    def __init__(
        self,
        llm: LLM,
        task_context: "Task",
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        """
        Initialize base role.

        Args:
            llm: LLM instance for generating responses
            task_context: Current task state and history
            llm_browser: Browser interface for page context
            throttler: Rate limiter for LLM calls
        """
        self.llm = llm
        self.task_context = task_context
        self.llm_browser = llm_browser
        self.throttler = throttler

    @abstractmethod
    async def _build_context(self) -> "Context":
        """
        Build role-specific context for LLM.

        Each role builds different context:
        - Proposer: task + tools + history + page (detailed)
        - Verifier: task + mark_complete tool + history + page
        - Planner: task + planning tools + history

        Returns:
            Context with system prompt and user blocks
        """
        pass

    async def propose_actions(self) -> Proposal:
        """
        Propose actions to take (thinking phase).

        Flow:
        1. Throttle
        2. Build context (role-specific)
        3. Update throttle
        4. Generate and validate JSON response (with automatic retry)

        Returns:
            Proposal with message, next_role, and actions

        Raises:
            ValueError: If validation fails after max retries
        """
        await self.throttler.wait()

        # Build context (role-specific)
        context = await self._build_context()
        self.throttler.update_timestamp()

        # Generate and validate response with automatic retry
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Generate JSON response
                response = await self.llm.generate(context, use_json=True)

                # Parse JSON (handles markdown fences)
                cleaned_json_dict = parse_json(response)

                # Validate with Pydantic
                return Proposal.model_validate(cleaned_json_dict)

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # If not the last attempt, append error feedback and retry
                if attempt < max_retries - 1:
                    error_type = type(e).__name__
                    error_msg = str(e)

                    # Append error feedback to context
                    feedback = (
                        f"\n❌ ERROR: Your previous JSON response was invalid.\n\n"
                        f"Error type: {error_type}\n"
                        f"Error details: {error_msg}\n\n"
                        f"Please provide a valid JSON response that matches the required schema."
                    )
                    context.append(Block(feedback))
                    # Loop continues with updated context
                else:
                    # Last attempt failed, raise error
                    raise ValueError(
                        f"Failed to parse LLM response after {max_retries} attempts. "
                        f"Last error: {type(e).__name__}: {str(e)}"
                    ) from last_error

        # Should never reach here
        raise last_error

    async def execute(self, actions: List[Action]) -> List[ActionResult]:
        """
        Execute proposed actions (doing phase).

        Uses this role's tool registry to execute actions.
        Each tool validates its own parameters.

        Args:
            actions: List of actions to execute

        Returns:
            List of execution results
        """
        results = []
        for action in actions:
            try:
                # Get tool from registry
                tool = self.tool_registry.get(action.tool)

                # Tool validates its own parameters (dict → ToolParams)
                validated_params = tool.params_class(**action.parameters)

                # Throttle before action
                await self.throttler.wait()

                # Execute with validated parameters
                await tool.execute(validated_params)

                # Update timestamp after action completes
                self.throttler.update_timestamp()
                results.append(ActionResult(success=True))

            except Exception as e:
                results.append(ActionResult(success=False, error=str(e)))

        return results
