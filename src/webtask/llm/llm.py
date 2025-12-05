"""LLM base class for conversation-based generation with tool calling support."""

import logging
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from .message import Message, Role

if TYPE_CHECKING:
    from webtask.llm.tool import Tool


class LLM(ABC):
    """Abstract base class for Large Language Models with conversation support."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> Message:
        """Generate response with tool calling.

        Args:
            messages: Conversation history as list of Message objects.
                Each message has a role (SYSTEM, USER, MODEL, TOOL) and content.
            tools: List of tools available for the LLM to call (required).

        Returns:
            Message with role=Role.MODEL containing content (Text/Image) and/or ToolCall.

        Example:
            >>> messages = [
            ...     Message(role=Role.SYSTEM, content=[Text(text="You are a web agent")]),
            ...     Message(role=Role.USER, content=[Text(text="Click the login button")]),
            ... ]
            >>> response = await llm.call_tools(messages, tools=[ClickTool(), NavigateTool()])
            >>> tool_calls = [c for c in response.content if isinstance(c, ToolCall)]
            >>> print(tool_calls[0].name)
            "click"

        Note:
            - Messages maintain conversation context across multiple turns
            - Tool calls are included in message content as ToolCall objects
            - Each LLM implementation handles its own API format conversion
        """
        pass
