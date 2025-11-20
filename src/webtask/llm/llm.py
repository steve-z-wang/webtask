"""LLM base class for conversation-based generation with tool calling support."""

import logging
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from .message import Message, AssistantMessage

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
    ) -> AssistantMessage:
        """Generate response with tool calling.

        Args:
            messages: Conversation history as list of Message objects.
                Can include SystemMessage, UserMessage, AssistantMessage, ToolResultMessage.
            tools: List of tools available for the LLM to call (required).

        Returns:
            AssistantMessage with content (text/images) and/or tool_calls.

        Example:
            >>> messages = [
            ...     SystemMessage(content=[TextContent(text="You are a web agent")]),
            ...     UserMessage(content=[TextContent(text="Click the login button")]),
            ... ]
            >>> response = await llm.call_tools(messages, tools=[ClickTool(), NavigateTool()])
            >>> print(response.tool_calls[0].name)
            "click"

        Note:
            - Messages maintain conversation context across multiple turns
            - Tool calls are returned in AssistantMessage.tool_calls
            - Each LLM implementation handles its own API format conversion
        """
        pass
