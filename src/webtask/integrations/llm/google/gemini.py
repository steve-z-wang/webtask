"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, Type, TypeVar, TYPE_CHECKING
import json
import time
from pydantic import BaseModel, ValidationError

import google.generativeai as genai
from google.generativeai import protos

from webtask.llm import LLM
from webtask.llm.message import (
    Message,
    AssistantMessage,
    TextContent,
    ToolCall,
)
from webtask._internal.utils.debug import LLMDebugger
from .gemini_converter import (
    messages_to_gemini_content,
    build_tool_declarations,
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
        self._debugger = LLMDebugger()

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

        generation_config = genai.GenerationConfig(temperature=self.temperature)

        tool_config = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(
                mode=protos.FunctionCallingConfig.Mode.AUTO,
            )
        )

        num_messages = len(gemini_content)
        total_parts = sum(len(msg.get("parts", [])) for msg in gemini_content)
        self.logger.info(
            f"Calling Gemini API - Messages: {num_messages}, Parts: {total_parts}, Tools: {len(tools)}"
        )

        start_time = time.time()
        try:
            response = await self.model.generate_content_async(
                gemini_content,
                generation_config=generation_config,
                tools=[gemini_tools],
                tool_config=tool_config,
            )
            self.logger.info(f"Gemini API responded in {time.time() - start_time:.2f}s")
        except Exception as e:
            self.logger.error(
                f"Gemini API error after {time.time() - start_time:.2f}s: {type(e).__name__}: {e}"
            )
            raise

        tool_calls = []
        content_parts = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    content_parts.append(TextContent(text=part.text))
                elif hasattr(part, "function_call") and part.function_call:
                    tool_calls.append(
                        ToolCall(
                            name=part.function_call.name,
                            arguments=dict(part.function_call.args),
                        )
                    )

        assistant_msg = AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None,
        )

        self._debugger.save_call(messages, assistant_msg)
        return assistant_msg

    async def generate_response(
        self,
        messages: List[Message],
        response_model: Type[T],
    ) -> T:
        """Generate structured JSON response."""
        gemini_content = messages_to_gemini_content(messages)

        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            response_mime_type="application/json",
        )

        num_messages = len(gemini_content)
        total_parts = sum(len(msg.get("parts", [])) for msg in gemini_content)
        self.logger.info(
            f"Calling Gemini API - Messages: {num_messages}, Parts: {total_parts}"
        )

        start_time = time.time()
        try:
            response = await self.model.generate_content_async(
                gemini_content,
                generation_config=generation_config,
            )
            self.logger.info(f"Gemini API responded in {time.time() - start_time:.2f}s")
        except Exception as e:
            self.logger.error(
                f"Gemini API error after {time.time() - start_time:.2f}s: {type(e).__name__}: {e}"
            )
            raise

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
