"""Google Gemini Computer Use LLM implementation."""

from typing import Optional, List, TYPE_CHECKING
import os
from google import genai
from google.genai import types
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
import base64

if TYPE_CHECKING:
    from webtask._internal.agent.tool import Tool


class GeminiComputerUseLLM(LLM):
    """
    Google Gemini Computer Use implementation of LLM.

    Uses Gemini's built-in computer use capabilities for browser automation.
    This implementation uses the newer google.genai.Client API with computer_use tools.
    """

    def __init__(
        self,
        client: genai.Client,
        model_name: str,
        temperature: float,
        config: types.GenerateContentConfig,
    ):
        """
        Initialize GeminiComputerUseLLM (use create factory instead).

        Args:
            client: Gemini Client instance
            model_name: Model name
            temperature: Temperature for generation
            config: GenerateContentConfig with computer_use tools
        """
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.temperature = temperature
        self.config = config

    @classmethod
    def create(
        cls,
        model: str = "gemini-2.5-computer-use-preview-10-2025",
        api_key: Optional[str] = None,
        temperature: float = 1.0,
        use_vertexai: bool = False,
        vertexai_project: Optional[str] = None,
        vertexai_location: Optional[str] = None,
        excluded_predefined_functions: Optional[List[str]] = None,
        custom_functions: Optional[List[types.FunctionDeclaration]] = None,
    ) -> "GeminiComputerUseLLM":
        """
        Create a GeminiComputerUseLLM instance.

        Args:
            model: Model name (default: "gemini-2.5-computer-use-preview-10-2025")
            api_key: Google API key (if None, uses GEMINI_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)
            use_vertexai: Whether to use Vertex AI (default: False)
            vertexai_project: Vertex AI project ID (required if use_vertexai=True)
            vertexai_location: Vertex AI location (required if use_vertexai=True)
            excluded_predefined_functions: List of predefined computer use functions to exclude
            custom_functions: List of custom function declarations to add

        Returns:
            GeminiComputerUseLLM instance

        Example:
            >>> llm = GeminiComputerUseLLM.create()
            >>> messages = [UserMessage(content=[TextContent(text="Go to google.com")])]
            >>> response = await llm.generate(messages)
        """
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        # Create client
        client = genai.Client(
            api_key=api_key,
            vertexai=use_vertexai,
            project=vertexai_project,
            location=vertexai_location,
        )

        # Build tools list
        tools = [
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=excluded_predefined_functions or [],
                ),
            )
        ]

        # Add custom functions if provided
        if custom_functions:
            tools.append(types.Tool(function_declarations=custom_functions))

        # Create generation config
        config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            tools=tools,
        )

        return cls(client, model, temperature, config)

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List["Tool"]] = None,
    ) -> AssistantMessage:
        """
        Generate response with computer use capabilities.

        Note: The tools parameter is currently ignored. Gemini Computer Use
        provides predefined browser functions (click_at, hover_at, type_text_at, etc.)
        that are automatically configured.

        Args:
            messages: Conversation history as list of Message objects
            tools: Optional list of tools (currently ignored for computer use)

        Returns:
            AssistantMessage with content and/or tool_calls
        """
        self.logger.debug(
            f"Calling Gemini Computer Use API - model: {self.model_name}, "
            f"temperature: {self.temperature}"
        )

        # Convert messages to Gemini format
        gemini_contents = self._convert_messages_to_gemini(messages)

        # Call Gemini API
        response = await self._generate_content_async(gemini_contents)

        # Log token usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini Computer Use API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        # Convert response to AssistantMessage
        return self._convert_response_to_assistant_message(response)

    async def _generate_content_async(
        self, contents: List[types.Content]
    ) -> types.GenerateContentResponse:
        """Call Gemini API with retry logic."""
        import asyncio

        max_retries = 5
        base_delay = 1

        for attempt in range(max_retries):
            try:
                # Note: The genai.Client doesn't have an async method, so we wrap in asyncio
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=contents,
                    config=self.config,
                )
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    self.logger.warning(
                        f"Generate content failed on attempt {attempt + 1}. "
                        f"Retrying in {delay} seconds... Error: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"Generate content failed after {max_retries} attempts"
                    )
                    raise

    def _convert_messages_to_gemini(
        self, messages: List[Message]
    ) -> List[types.Content]:
        """Convert our Message types to Gemini Content format."""
        gemini_contents = []
        system_parts = []

        for message in messages:
            if isinstance(message, SystemMessage):
                # Store system message parts to prepend to first user message
                for content in message.content:
                    if isinstance(content, TextContent):
                        system_parts.append(types.Part(text=content.text))
                    elif isinstance(content, ImageContent):
                        system_parts.append(
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=content.mime_type,
                                    data=base64.b64decode(content.data),
                                )
                            )
                        )

            elif isinstance(message, UserMessage):
                parts = []

                # Prepend system instruction if exists
                if system_parts:
                    parts.extend(system_parts)
                    system_parts = []

                # Add user message content
                for content in message.content:
                    if isinstance(content, TextContent):
                        parts.append(types.Part(text=content.text))
                    elif isinstance(content, ImageContent):
                        parts.append(
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=content.mime_type,
                                    data=base64.b64decode(content.data),
                                )
                            )
                        )

                gemini_contents.append(types.Content(role="user", parts=parts))

            elif isinstance(message, AssistantMessage):
                parts = []

                # Add text content
                if message.content:
                    for content in message.content:
                        if isinstance(content, TextContent):
                            parts.append(types.Part(text=content.text))

                # Add tool calls as function calls
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        parts.append(
                            types.Part(
                                function_call=types.FunctionCall(
                                    name=tool_call.name, args=tool_call.arguments
                                )
                            )
                        )

                gemini_contents.append(types.Content(role="model", parts=parts))

            elif isinstance(message, ToolResultMessage):
                parts = []

                for result in message.results:
                    # Build function response
                    response_dict = {}
                    response_parts = []

                    # Extract text and images from result content
                    for content in result.content:
                        if isinstance(content, TextContent):
                            # Try to parse text as structured response
                            import json

                            try:
                                response_dict.update(json.loads(content.text))
                            except (json.JSONDecodeError, ValueError):
                                # If not JSON, add as text part
                                response_parts.append(types.Part(text=content.text))
                        elif isinstance(content, ImageContent):
                            # Screenshots from computer use actions
                            response_parts.append(
                                types.FunctionResponsePart(
                                    inline_data=types.FunctionResponseBlob(
                                        mime_type=content.mime_type,
                                        data=base64.b64decode(content.data),
                                    )
                                )
                            )

                    # Create function response
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=result.name,
                                response=response_dict if response_dict else {},
                                parts=response_parts if response_parts else None,
                            )
                        )
                    )

                gemini_contents.append(types.Content(role="user", parts=parts))

        return gemini_contents

    def _convert_response_to_assistant_message(
        self, response: types.GenerateContentResponse
    ) -> AssistantMessage:
        """Convert Gemini response to AssistantMessage."""
        if not response.candidates:
            raise ValueError("Empty response from Gemini Computer Use")

        candidate = response.candidates[0]
        content_parts = []
        tool_calls = []

        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    content_parts.append(TextContent(text=part.text))
                elif part.function_call:
                    # Convert function call to tool call
                    tool_calls.append(
                        ToolCall(
                            id=None,  # Gemini doesn't provide IDs
                            name=part.function_call.name,
                            arguments=dict(part.function_call.args),
                        )
                    )

        return AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None,
        )
