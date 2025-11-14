"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, Dict, Any, Type, TypeVar, TYPE_CHECKING
import json
from PIL import Image as PILImage
import io
import base64
from pydantic import BaseModel, ValidationError

import google.generativeai as genai
from google.generativeai import types
from google.generativeai import protos

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
)

if TYPE_CHECKING:
    from webtask.agent.tool import Tool

T = TypeVar("T", bound=BaseModel)


class GeminiLLM(LLM):
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
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> "GeminiLLM":
        """
        Create a GeminiLLM instance.

        Args:
            model: Model name (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            GeminiLLM instance

        Example:
            >>> llm = GeminiLLM.create(model="gemini-2.0-flash-exp")
            >>> messages = [SystemMessage(content=[TextContent(text="You are helpful")])]
            >>> response = await llm.generate(messages, tools=[])
        """
        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)

        # Create model (generation config set per request)
        gemini_model = genai.GenerativeModel(model_name=model)

        return cls(gemini_model, model, temperature)

    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean Pydantic JSON schema to be compatible with Gemini.

        Gemini only accepts a subset of JSON schema fields. We need to remove
        unsupported fields like title, maximum, minimum, maxLength, etc.
        """
        # Fields that Gemini supports
        allowed_fields = {
            "type",
            "description",
            "enum",
            "items",
            "properties",
            "required",
            "nullable",
            "format",
        }

        # Create cleaned schema
        cleaned = {}

        for key, value in schema.items():
            if key in allowed_fields:
                if key == "properties" and isinstance(value, dict):
                    # Recursively clean nested properties
                    cleaned[key] = {
                        prop_name: self._clean_schema_for_gemini(prop_schema)
                        for prop_name, prop_schema in value.items()
                    }
                elif key == "items" and isinstance(value, dict):
                    # Recursively clean array items schema
                    cleaned[key] = self._clean_schema_for_gemini(value)
                else:
                    cleaned[key] = value

        return cleaned

    def _build_tool_declarations(self, tools: List["Tool"]) -> types.Tool:
        """Build Gemini function declarations from tools."""
        function_declarations = []

        for tool in tools:
            # Convert Pydantic model to JSON schema
            params_schema = tool.Params.model_json_schema()

            # Clean schema to be Gemini-compatible
            params_schema = self._clean_schema_for_gemini(params_schema)

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
                if msg.content:
                    system_text = "\n\n".join([part.text for part in msg.content])

            elif isinstance(msg, UserMessage):
                # Build parts list (text and images)
                parts = []

                # Prepend system text to first user message
                if system_text:
                    parts.append(system_text)
                    system_text = None  # Only add once

                if msg.content:
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
                        function_call = protos.Part(
                            function_call=protos.FunctionCall(
                                name=tc.name,
                                args=tc.arguments,
                            )
                        )
                        parts.append(function_call)

                if parts:
                    gemini_messages.append({"role": "model", "parts": parts})

            elif isinstance(msg, ToolResultMessage):
                # Tool results - convert to function responses
                parts = []

                # Add function responses for each tool result
                for result in msg.results:
                    response_data = {
                        "status": result.status.value,
                    }
                    if result.output is not None:
                        response_data["output"] = result.output
                    if result.error:
                        response_data["error"] = result.error

                    function_response = protos.Part(
                        function_response=protos.FunctionResponse(
                            name=result.name,
                            response=response_data,
                        )
                    )
                    parts.append(function_response)

                # Add observation content (DOM + screenshot)
                if msg.content:
                    for content_part in msg.content:
                        if isinstance(content_part, TextContent):
                            parts.append(content_part.text)
                        elif isinstance(content_part, ImageContent):
                            image_bytes = base64.b64decode(content_part.data)
                            pil_image = PILImage.open(io.BytesIO(image_bytes))
                            parts.append(pil_image)

                gemini_messages.append({"role": "user", "parts": parts})

        return gemini_messages

    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> AssistantMessage:
        """
        Generate response with tool calling (for Worker/Verifier).

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

        # Create tool config to force function calling using protos
        tool_config = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(
                mode=protos.FunctionCallingConfig.Mode.ANY,
            )
        )

        # Call Gemini API with tools
        response = await self.model.generate_content_async(
            gemini_content,
            generation_config=generation_config,
            tools=[gemini_tools],
            tool_config=tool_config,
        )

        # Log token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        # Debug: Log response structure
        self.logger.debug(
            f"Response candidates: {len(response.candidates) if response.candidates else 0}"
        )
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            self.logger.debug(f"Candidate content: {candidate.content}")
            if candidate.content and candidate.content.parts:
                self.logger.debug(f"Parts count: {len(candidate.content.parts)}")
                for i, part in enumerate(candidate.content.parts):
                    self.logger.debug(f"Part {i}: {type(part).__name__}")
                    if hasattr(part, "function_call"):
                        self.logger.debug(f"  Has function_call: {part.function_call}")
                    if hasattr(part, "text"):
                        self.logger.debug(
                            f"  Has text: {part.text[:200] if part.text else None}"
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

    async def generate_response(
        self,
        messages: List[Message],
        response_model: Type[T],
    ) -> T:
        """
        Generate structured JSON response (for NaturalSelector).

        Uses Gemini's JSON mode to get structured output matching response_model.

        Args:
            messages: Conversation history as list of Message objects
            response_model: Pydantic model class for structured output

        Returns:
            Instance of response_model with parsed LLM response
        """
        self.logger.debug(
            f"Calling Gemini API (JSON mode) - model: {self.model_name}, "
            f"temperature: {self.temperature}, "
            f"messages: {len(messages)}, response_model: {response_model.__name__}"
        )

        # Convert messages to Gemini format
        gemini_content = self._messages_to_gemini_content(messages)

        # Get JSON schema from response_model
        schema = response_model.model_json_schema()

        # Clean schema to be Gemini-compatible
        schema = self._clean_schema_for_gemini(schema)

        # Create generation config with JSON mode
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )

        # Call Gemini API
        response = await self.model.generate_content_async(
            gemini_content,
            generation_config=generation_config,
        )

        # Log token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        # Extract text response
        if not response.candidates or len(response.candidates) == 0:
            raise ValueError("No response candidates from Gemini")

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            raise ValueError("No content in Gemini response")

        text_response = candidate.content.parts[0].text
        self.logger.debug(f"Gemini JSON response: {text_response[:500]}")

        # Parse JSON and validate against response_model
        try:
            response_dict = json.loads(text_response)
            return response_model.model_validate(response_dict)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Failed to parse Gemini response as {response_model.__name__}: {e}"
            ) from e
