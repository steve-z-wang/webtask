"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, Dict, Any
import json
import logging
from PIL import Image as PILImage
import io
import base64

import google.generativeai as genai
from google.generativeai import types

from webtask.llm import LLM
from webtask.llm.message import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
    ToolCall,
    ImageMimeType,
)
from webtask.agent.tool import Tool


class GeminiLLMV2(LLM):
    """
    Google Gemini implementation with conversation-based interface.

    Uses structured JSON output with optional observation/thinking fields
    and validates tool calls against provided tools.
    """

    def __init__(
        self,
        model: genai.GenerativeModel,
        model_name: str,
        temperature: float,
    ):
        """
        Initialize GeminiLLMV2 (use create factory instead).

        Args:
            model: Gemini GenerativeModel instance
            model_name: Model name
            temperature: Temperature for generation
        """
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.model = model

    @classmethod
    def create(
        cls,
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> "GeminiLLMV2":
        """
        Create a GeminiLLMV2 instance.

        Args:
            model: Model name (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            GeminiLLMV2 instance

        Example:
            >>> llm = GeminiLLMV2.create(model="gemini-2.0-flash-exp")
            >>> messages = [SystemMessage(content=[TextContent(text="You are helpful")])]
            >>> response = await llm.generate(messages, tools=[])
        """
        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)

        # Create model (generation config set per request)
        gemini_model = genai.GenerativeModel(model_name=model)

        return cls(gemini_model, model, temperature)

    def _build_tool_declarations(self, tools: List[Tool]) -> types.Tool:
        """Build Gemini function declarations from tools."""
        function_declarations = []

        for tool in tools:
            # Convert Pydantic model to JSON schema
            params_schema = tool.Params.model_json_schema()

            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=params_schema,
                )
            )

        return types.Tool(function_declarations=function_declarations)

    def _messages_to_gemini_content(
        self, messages: List[Message]
    ) -> List[types.ContentDict]:
        """
        Convert Message history to Gemini's content format.

        Gemini uses alternating user/model roles. System messages are
        combined with the first user message.
        """
        gemini_messages = []
        system_text = None

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Extract system text (to be prepended to first user message)
                system_text = "\n\n".join([part.text for part in msg.content])

            elif isinstance(msg, UserMessage):
                # Build parts list (text and images)
                parts = []

                # Prepend system text to first user message
                if system_text:
                    parts.append(system_text)
                    system_text = None  # Only add once

                for content_part in msg.content:
                    if isinstance(content_part, TextContent):
                        parts.append(content_part.text)
                    elif isinstance(content_part, ImageContent):
                        # Convert base64 to PIL Image
                        image_bytes = base64.b64decode(content_part.data)
                        pil_image = PILImage.open(io.BytesIO(image_bytes))
                        parts.append(pil_image)

                gemini_messages.append({"role": "user", "parts": parts})

            elif isinstance(msg, AssistantMessage):
                # Assistant message with tool calls
                # Gemini expects function calls in a specific format
                parts = []

                # Include content if present
                if msg.content:
                    for content_part in msg.content:
                        if isinstance(content_part, TextContent):
                            parts.append(content_part.text)
                        elif isinstance(content_part, ImageContent):
                            image_bytes = base64.b64decode(content_part.data)
                            pil_image = PILImage.open(io.BytesIO(image_bytes))
                            parts.append(pil_image)

                # Include tool calls as function calls
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        function_call = types.FunctionCall(
                            name=tc.name,
                            args=tc.arguments,
                        )
                        parts.append(function_call)

                if parts:
                    gemini_messages.append({"role": "model", "parts": parts})

            elif isinstance(msg, ToolResultMessage):
                # Tool results - convert to function responses
                parts = []

                # Add function responses for each tool result
                for result in msg.results:
                    function_response = types.FunctionResponse(
                        name=result.name,
                        response={
                            "status": result.status,
                            "error": result.error if result.error else None,
                        },
                    )
                    parts.append(function_response)

                # Add page state content (DOM + screenshot)
                for content_part in msg.content:
                    if isinstance(content_part, TextContent):
                        parts.append(content_part.text)
                    elif isinstance(content_part, ImageContent):
                        image_bytes = base64.b64decode(content_part.data)
                        pil_image = PILImage.open(io.BytesIO(image_bytes))
                        parts.append(pil_image)

                gemini_messages.append({"role": "user", "parts": parts})

        return gemini_messages

    async def generate(
        self,
        messages: List[Message],
        tools: List[Tool],
    ) -> AssistantMessage:
        """
        Generate response from conversation history with tool calling.

        Uses Gemini's native function calling to get tool calls.

        Args:
            messages: Conversation history as list of Message objects
            tools: List of tools available for the LLM to call

        Returns:
            AssistantMessage with tool_calls
        """
        self.logger.debug(
            f"Calling Gemini API - model: {self.model_name}, "
            f"temperature: {self.temperature}, "
            f"messages: {len(messages)}, tools: {len(tools)}"
        )

        # Convert messages to Gemini format
        gemini_content = self._messages_to_gemini_content(messages)

        # Build tool declarations
        gemini_tools = self._build_tool_declarations(tools)

        # Create generation config
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
        )

        # Call Gemini API with tools
        response = await self.model.generate_content_async(
            gemini_content,
            generation_config=generation_config,
            tools=[gemini_tools],
        )

        # Log token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        # Extract tool calls from response
        tool_calls = []
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if part has function_call
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        tool_calls.append(
                            ToolCall(
                                name=fc.name,
                                arguments=dict(fc.args),
                            )
                        )

        # Create AssistantMessage
        return AssistantMessage(
            tool_calls=tool_calls if tool_calls else None,
        )
