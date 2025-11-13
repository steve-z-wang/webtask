"""OpenAI LLM implementation."""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from openai import AsyncOpenAI
from ....llm import LLM
from ....llm.message import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ToolCall,
    ToolResult,
)

if TYPE_CHECKING:
    from webtask._internal.agent.tool import Tool


class OpenAILLM(LLM):
    """
    OpenAI implementation of LLM.

    Wraps OpenAI's API for text generation (GPT-4, GPT-3.5, etc.).
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        temperature: float,
    ):
        """
        Initialize OpenAILLM (use create factory instead).

        Args:
            client: AsyncOpenAI client instance
            model: Model name
            temperature: Temperature for generation
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.client = client

    @classmethod
    def create(
        cls,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 1,
    ) -> "OpenAILLM":
        """
        Create an OpenAILLM instance.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            OpenAILLM instance

        Example:
            >>> llm = OpenAILLM.create(model="gpt-4")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        client = AsyncOpenAI(api_key=api_key)
        return cls(client, model, temperature)

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List["Tool"]] = None,
    ) -> AssistantMessage:
        """
        Generate response with optional tool calling support.

        Args:
            messages: Conversation history as list of Message objects
            tools: Optional list of tools available for the LLM to call

        Returns:
            AssistantMessage with content (text/images) and/or tool_calls
        """
        self.logger.debug(
            f"Calling OpenAI API - model: {self.model}, temperature: {self.temperature}, "
            f"tools: {len(tools) if tools else 0}"
        )

        # Convert messages to OpenAI format
        openai_messages = self._convert_messages_to_openai(messages)

        # Build API call kwargs
        api_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
        }

        # Add tools if provided
        if tools:
            api_kwargs["tools"] = self._convert_tools_to_openai(tools)
            api_kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**api_kwargs)

        # Log token usage if available
        if response.usage:
            self.logger.debug(
                f"OpenAI API response - "
                f"prompt_tokens: {response.usage.prompt_tokens}, "
                f"completion_tokens: {response.usage.completion_tokens}, "
                f"total_tokens: {response.usage.total_tokens}"
            )

        # Convert response to AssistantMessage
        return self._convert_response_to_assistant_message(response)

    def _convert_messages_to_openai(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert our Message types to OpenAI format."""
        openai_messages = []

        for message in messages:
            if isinstance(message, SystemMessage):
                # OpenAI supports system messages
                content = []
                for content_part in message.content:
                    if isinstance(content_part, TextContent):
                        content.append({"type": "text", "text": content_part.text})
                    elif isinstance(content_part, ImageContent):
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_part.mime_type};base64,{content_part.data}"
                            }
                        })

                # If single text content, use string directly
                if len(content) == 1 and content[0]["type"] == "text":
                    openai_messages.append({"role": "system", "content": content[0]["text"]})
                else:
                    openai_messages.append({"role": "system", "content": content})

            elif isinstance(message, UserMessage):
                content = []
                for content_part in message.content:
                    if isinstance(content_part, TextContent):
                        content.append({"type": "text", "text": content_part.text})
                    elif isinstance(content_part, ImageContent):
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_part.mime_type};base64,{content_part.data}"
                            }
                        })

                # If single text content, use string directly
                if len(content) == 1 and content[0]["type"] == "text":
                    openai_messages.append({"role": "user", "content": content[0]["text"]})
                else:
                    openai_messages.append({"role": "user", "content": content})

            elif isinstance(message, AssistantMessage):
                msg: Dict[str, Any] = {"role": "assistant"}

                # Add text content if present
                if message.content:
                    text_parts = [c.text for c in message.content if isinstance(c, TextContent)]
                    if text_parts:
                        msg["content"] = " ".join(text_parts)

                # Add tool calls if present
                if message.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": str(tc.arguments)  # OpenAI expects JSON string
                            }
                        }
                        for tc in message.tool_calls
                    ]

                openai_messages.append(msg)

            elif isinstance(message, ToolResultMessage):
                # OpenAI uses separate messages for each tool result
                for result in message.results:
                    # Build content from text/images
                    content_parts = []
                    for content_part in result.content:
                        if isinstance(content_part, TextContent):
                            content_parts.append(content_part.text)

                    content_str = " ".join(content_parts) if content_parts else "success"

                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": result.tool_call_id,
                        "content": content_str
                    })

        return openai_messages

    def _convert_tools_to_openai(self, tools: List["Tool"]) -> List[Dict[str, Any]]:
        """Convert our Tool types to OpenAI format."""
        openai_tools = []

        for tool in tools:
            # Get Pydantic schema from tool.Params
            params_schema = tool.Params.model_json_schema()
            properties = params_schema.get("properties", {})
            required = params_schema.get("required", [])

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })

        return openai_tools

    def _convert_response_to_assistant_message(self, response) -> AssistantMessage:
        """Convert OpenAI response to AssistantMessage."""
        if not response.choices:
            raise ValueError("Empty response from OpenAI")

        choice = response.choices[0]
        message = choice.message

        content_parts = []
        tool_calls = []

        # Extract text content
        if message.content:
            content_parts.append(TextContent(text=message.content))

        # Extract tool calls
        if message.tool_calls:
            import json
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

        return AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None
        )
