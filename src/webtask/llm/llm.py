"""LLM base class for conversation-based generation with tool calling support."""

import logging
from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, TYPE_CHECKING
from pydantic import BaseModel
from .message import Message, AssistantMessage

if TYPE_CHECKING:
    from webtask.agent.tool import Tool

T = TypeVar("T", bound=BaseModel)


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
        """Generate response with tool calling (for Worker/Verifier).

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

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        response_model: Type[T],
    ) -> T:
        """Generate structured JSON response (for NaturalSelector).

        Args:
            messages: Conversation history as list of Message objects.
            response_model: Pydantic model class for structured output.

        Returns:
            Instance of response_model with parsed LLM response.

        Example:
            >>> messages = [
            ...     SystemMessage(content=[TextContent(text="You are a selector")]),
            ...     UserMessage(content=[TextContent(text="Find the login button")]),
            ... ]
            >>> response = await llm.generate_response(messages, SelectorResponse)
            >>> print(response.element_id)
            "button-5"

        Note:
            - LLM must return valid JSON matching response_model schema
            - Implementation should handle validation and retries
        """
        pass
