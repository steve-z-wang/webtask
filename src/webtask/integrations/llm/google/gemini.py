"""Google Gemini LLM implementation."""

from typing import Optional, List, TYPE_CHECKING
import google.generativeai as genai
from google.generativeai import types as genai_types
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
import io
from PIL import Image as PILImage

if TYPE_CHECKING:
    from webtask._internal.agent.tool import Tool


class GeminiLLM(LLM):
    """
    Google Gemini implementation of LLM.

    Wraps Google's Gemini API for text generation.
    """

    def __init__(
        self,
        model: genai.GenerativeModel,
        model_name: str,
        temperature: float,
    ):
        """
        Initialize GeminiLLM (use create factory instead).

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
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> "GeminiLLM":
        """
        Create a GeminiLLM instance.

        Args:
            model: Model name (e.g., "gemini-2.5-flash", "gemini-1.5-pro")
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            GeminiLLM instance

        Example:
            >>> llm = GeminiLLM.create(model="gemini-2.5-flash")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)

        # Create model with generation config
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            ),
        )

        return cls(gemini_model, model, temperature)

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
            f"Calling Gemini API - model: {self.model_name}, temperature: {self.temperature}, "
            f"tools: {len(tools) if tools else 0}"
        )

        # Convert messages to Gemini format
        gemini_contents = self._convert_messages_to_gemini(messages)

        # Convert tools to Gemini function declarations if provided
        gemini_tools = None
        if tools:
            gemini_tools = [self._convert_tools_to_gemini(tools)]

        # Call Gemini API
        response = await self.model.generate_content_async(
            gemini_contents,
            tools=gemini_tools
        )

        # Log token usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        # Convert response to AssistantMessage
        return self._convert_response_to_assistant_message(response)

    def _convert_messages_to_gemini(self, messages: List[Message]) -> List[genai_types.Content]:
        """Convert our Message types to Gemini Content format."""
        gemini_contents = []
        system_instruction = None

        for message in messages:
            if isinstance(message, SystemMessage):
                # Gemini handles system messages separately
                # For now, prepend to first user message
                system_parts = []
                for content in message.content:
                    if isinstance(content, TextContent):
                        system_parts.append(genai_types.Part(text=content.text))
                    elif isinstance(content, ImageContent):
                        pil_image = self._base64_to_pil(content.data)
                        system_parts.append(genai_types.Part(inline_data=genai_types.Blob(
                            mime_type=content.mime_type,
                            data=base64.b64decode(content.data)
                        )))

                # Store system instruction to prepend later
                system_instruction = system_parts

            elif isinstance(message, UserMessage):
                parts = []

                # Prepend system instruction if exists
                if system_instruction:
                    parts.extend(system_instruction)
                    system_instruction = None

                for content in message.content:
                    if isinstance(content, TextContent):
                        parts.append(genai_types.Part(text=content.text))
                    elif isinstance(content, ImageContent):
                        pil_image = self._base64_to_pil(content.data)
                        parts.append(genai_types.Part(inline_data=genai_types.Blob(
                            mime_type=content.mime_type,
                            data=base64.b64decode(content.data)
                        )))

                gemini_contents.append(genai_types.Content(role="user", parts=parts))

            elif isinstance(message, AssistantMessage):
                parts = []

                # Add text content
                if message.content:
                    for content in message.content:
                        if isinstance(content, TextContent):
                            parts.append(genai_types.Part(text=content.text))

                # Add tool calls as function calls
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        parts.append(genai_types.Part(
                            function_call=genai_types.FunctionCall(
                                name=tool_call.name,
                                args=tool_call.arguments
                            )
                        ))

                gemini_contents.append(genai_types.Content(role="model", parts=parts))

            elif isinstance(message, ToolResultMessage):
                parts = []

                for result in message.results:
                    # Build function response parts
                    response_parts = []
                    for content in result.content:
                        if isinstance(content, TextContent):
                            response_parts.append(genai_types.Part(text=content.text))
                        elif isinstance(content, ImageContent):
                            response_parts.append(genai_types.Part(inline_data=genai_types.Blob(
                                mime_type=content.mime_type,
                                data=base64.b64decode(content.data)
                            )))

                    # Gemini uses function name for matching (no IDs)
                    parts.append(genai_types.Part(
                        function_response=genai_types.FunctionResponse(
                            name=result.name,
                            response={"result": "success"},  # Simplified for now
                            parts=response_parts if response_parts else None
                        )
                    ))

                gemini_contents.append(genai_types.Content(role="user", parts=parts))

        return gemini_contents

    def _convert_tools_to_gemini(self, tools: List["Tool"]) -> genai_types.Tool:
        """Convert our Tool types to Gemini function declarations."""
        function_declarations = []

        for tool in tools:
            # Get Pydantic schema from tool.Params
            params_schema = tool.Params.model_json_schema()
            properties = params_schema.get("properties", {})
            required = params_schema.get("required", [])

            # Convert to Gemini format
            function_declarations.append(genai_types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        key: genai_types.Schema(
                            type=self._json_type_to_gemini_type(prop.get("type")),
                            description=prop.get("description", "")
                        )
                        for key, prop in properties.items()
                    },
                    required=required
                )
            ))

        return genai_types.Tool(function_declarations=function_declarations)

    def _convert_response_to_assistant_message(self, response) -> AssistantMessage:
        """Convert Gemini response to AssistantMessage."""
        if not response.candidates:
            raise ValueError("Empty response from Gemini")

        candidate = response.candidates[0]
        content_parts = []
        tool_calls = []

        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    content_parts.append(TextContent(text=part.text))
                elif part.function_call:
                    tool_calls.append(ToolCall(
                        id=None,  # Gemini doesn't provide IDs
                        name=part.function_call.name,
                        arguments=dict(part.function_call.args)
                    ))

        return AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None
        )

    def _base64_to_pil(self, data: str) -> PILImage.Image:
        """Convert base64 string to PIL Image."""
        image_bytes = base64.b64decode(data)
        return PILImage.open(io.BytesIO(image_bytes))

    def _json_type_to_gemini_type(self, json_type: str) -> genai_types.Type:
        """Convert JSON schema type to Gemini type."""
        mapping = {
            "string": genai_types.Type.STRING,
            "integer": genai_types.Type.INTEGER,
            "number": genai_types.Type.NUMBER,
            "boolean": genai_types.Type.BOOLEAN,
            "array": genai_types.Type.ARRAY,
            "object": genai_types.Type.OBJECT,
        }
        return mapping.get(json_type, genai_types.Type.STRING)
