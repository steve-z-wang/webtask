"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, TYPE_CHECKING

from google import genai
from google.genai import types

from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage
from webtask._internal.utils.context_debugger import LLMContextDebugger
from .gemini_mapper import (
    messages_to_gemini_content,
    build_tool_config,
    gemini_response_to_assistant_message,
)

if TYPE_CHECKING:
    from webtask.llm.tool import Tool


class Gemini(LLM):
    """Google Gemini implementation with conversation-based interface."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.5,
    ):
        """Initialize Gemini.

        Args:
            model: Gemini model name (e.g., "gemini-2.5-flash", "gemini-2.5-pro")
            api_key: Optional API key (if not set via environment variable)
            temperature: Sampling temperature (0.0 to 1.0)
        """
        super().__init__()

        # Create client - will use GEMINI_API_KEY or GOOGLE_API_KEY env var if not provided
        self._client = genai.Client(api_key=api_key) if api_key else genai.Client()

        self.model_name = model
        self.temperature = temperature
        self._debugger = LLMContextDebugger()

    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> AssistantMessage:
        """Generate response with tool calling."""
        gemini_content, system_instruction = messages_to_gemini_content(messages)
        tool_config = build_tool_config(tools)

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
            tools=[tool_config],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True  # We handle function calling ourselves
            ),
        )

        # Use async client
        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=config,
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
