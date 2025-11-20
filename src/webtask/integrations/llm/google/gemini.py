"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, TYPE_CHECKING

import google.generativeai as genai
from google.generativeai import protos

from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage
from webtask._internal.utils.context_debugger import LLMContextDebugger
from .gemini_mapper import (
    messages_to_gemini_content,
    build_tool_declarations,
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

        if api_key:
            genai.configure(api_key=api_key)  # type: ignore[attr-defined]

        self.model_name = model
        self.temperature = temperature
        self.model = genai.GenerativeModel(model_name=model)  # type: ignore[attr-defined]
        self._debugger = LLMContextDebugger()

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
