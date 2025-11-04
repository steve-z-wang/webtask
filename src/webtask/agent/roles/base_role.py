"""Base class for agent roles."""

from abc import ABC, abstractmethod
from typing import List
from ...llm import ValidatedLLM
from ..task import Task
from ...llm_browser import LLMBrowser
from ...utils.throttler import Throttler
from ..schemas.mode import Proposal
from ..schemas.actions import Action
from ..step import ExecutionResult


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
    - ValidatedLLM for reliable JSON responses
    - Task context for task state
    - LLMBrowser for page access
    - Throttler for rate limiting
    """

    def __init__(
        self,
        validated_llm: ValidatedLLM,
        task_context: Task,
        llm_browser: LLMBrowser,
        throttler: Throttler,
    ):
        """
        Initialize base role.

        Args:
            validated_llm: LLM wrapper with validation and retry
            task_context: Current task state and history
            llm_browser: Browser interface for page context
            throttler: Rate limiter for LLM calls
        """
        self.validated_llm = validated_llm
        self.task_context = task_context
        self.llm_browser = llm_browser
        self.throttler = throttler

    @abstractmethod
    async def propose_actions(self) -> Proposal:
        """
        Propose actions to take (thinking phase).

        Flow:
        1. Wait for throttle
        2. Build context
        3. Call LLM with validation
        4. Update throttle timestamp
        5. Return proposal

        Returns:
            Proposal with message, next_mode, and actions
        """
        pass

    async def execute(self, actions: List[Action]) -> List[ExecutionResult]:
        """
        Execute proposed actions (doing phase).

        Uses this role's tool registry to execute actions.

        Args:
            actions: List of actions to execute

        Returns:
            List of execution results
        """
        results = []
        for action in actions:
            try:
                tool = self.tool_registry.get(action.tool)
                # Throttle before action
                await self.throttler.wait()
                # action.parameters is already a validated Pydantic model
                await tool.execute(action.parameters)
                # Update timestamp after action completes
                self.throttler.update_timestamp()
                results.append(ExecutionResult(success=True))

            except Exception as e:
                results.append(ExecutionResult(success=False, error=str(e)))

        return results
