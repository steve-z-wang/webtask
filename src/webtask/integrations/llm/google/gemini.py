"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, Type, TypeVar, TYPE_CHECKING
import json
from pydantic import BaseModel, ValidationError

import google.generativeai as genai
from google.generativeai import protos

from webtask.llm import LLM
from webtask.llm.message import Message, UserMessage, AssistantMessage, TextContent
from webtask._internal.utils.context_debugger import LLMContextDebugger
from .gemini_mapper import (
    messages_to_gemini_content,
    build_tool_declarations,
    gemini_response_to_assistant_message,
)

if TYPE_CHECKING:
    from webtask.agent.tool import Tool

T = TypeVar("T", bound=BaseModel)


class GeminiLLM(LLM):
    """Google Gemini implementation with conversation-based interface."""

    def __init__(
        self,
        model: genai.GenerativeModel,
        model_name: str,
        temperature: float,
    ):
        """Initialize GeminiLLM (use create factory instead)."""
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.model = model
        self._debugger = LLMContextDebugger()

    @classmethod
    def create(
        cls,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.5,
    ) -> "GeminiLLM":
        """Create a GeminiLLM instance."""
        if api_key:
            genai.configure(api_key=api_key)  # type: ignore[attr-defined]

        gemini_model = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=model
        )

        return cls(gemini_model, model, temperature)

    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> AssistantMessage:
        """Generate response with tool calling."""
        gemini_content = messages_to_gemini_content(messages)
        gemini_tools = build_tool_declarations(tools)

        generation_config = genai.GenerationConfig(  # type: ignore[attr-defined]
            temperature=self.temperature
        )

        tool_config = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(
                mode=protos.FunctionCallingConfig.Mode.AUTO,
            )
        )

        response = await self.model.generate_content_async(
            gemini_content,
            generation_config=generation_config,
            tools=[gemini_tools],
            tool_config=tool_config,
        )

        # Log token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            self.logger.info(
                f"Token usage - Prompt: {usage.prompt_token_count}, "
                f"Response: {usage.candidates_token_count}, "
                f"Total: {usage.total_token_count}"
            )

        assistant_msg = gemini_response_to_assistant_message(response)
        self._debugger.save_call(messages, assistant_msg)
        return assistant_msg

    async def generate_response(
        self,
        messages: List[Message],
        response_model: Type[T],
    ) -> T:
        """Generate structured JSON response."""
        # Inject schema into messages
        schema = response_model.model_json_schema()
        schema_text = f"\n\nYou MUST respond with valid JSON matching this schema:\n```json\n{json.dumps(schema, indent=2)}\n```"

        messages_with_schema = messages + [
            UserMessage(content=[TextContent(text=schema_text)])
        ]

        gemini_content = messages_to_gemini_content(messages_with_schema)

        generation_config = genai.GenerationConfig(  # type: ignore[attr-defined]
            temperature=self.temperature,
            response_mime_type="application/json",
        )

        response = await self.model.generate_content_async(
            gemini_content,
            generation_config=generation_config,
        )

        # Log token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            self.logger.info(
                f"Token usage - Prompt: {usage.prompt_token_count}, "
                f"Response: {usage.candidates_token_count}, "
                f"Total: {usage.total_token_count}"
            )

        if not response.candidates or not response.candidates[0].content:
            raise ValueError("No response from Gemini")

        text_response = response.candidates[0].content.parts[0].text

        try:
            result = response_model.model_validate(json.loads(text_response))
            self._debugger.save_call(
                messages, AssistantMessage(content=[TextContent(text=text_response)])
            )
            return result
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Failed to parse Gemini response as {response_model.__name__}: {e}"
            ) from e
