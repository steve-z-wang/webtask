"""Base class for agent modes."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from ...llm import ValidatedLLM, Context
from ..task import Task
from ...llm_browser import LLMBrowser
from ..throttler import Throttler

# Type variable for mode result
T = TypeVar("T")


class BaseMode(ABC, Generic[T]):
    """
    Base class for agent modes (Verify, Propose, Plan, etc.).

    Each mode has:
    - Different context building (what info to send to LLM)
    - Different response schema (what LLM returns)
    - Different prompts (how to instruct LLM)

    All modes share:
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
        Initialize base mode.

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
    async def execute(self) -> T:
        """
        Execute this mode and return mode-specific result.

        Flow:
        1. Wait for throttle
        2. Build context
        3. Call LLM with validation
        4. Update throttle timestamp
        5. Return result

        Returns:
            Mode-specific result (VerifyResult, ProposeResult, etc.)
        """
        pass
