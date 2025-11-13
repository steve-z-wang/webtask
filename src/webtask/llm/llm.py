"""LLM base class for text generation."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from .message import Message, AssistantMessage

if TYPE_CHECKING:
    from webtask._internal.agent.tool import Tool


class LLM(ABC):
    """Abstract base class for Large Language Models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List["Tool"]] = None,
    ) -> AssistantMessage:
        """Generate response with optional tool calling support.

        Args:
            messages: Conversation history as list of Message objects
            tools: Optional list of tools available for the LLM to call

        Returns:
            AssistantMessage with content (text/images) and/or tool_calls
        """
        pass
