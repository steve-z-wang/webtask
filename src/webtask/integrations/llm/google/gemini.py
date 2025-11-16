"""Google Gemini LLM implementation with conversation-based interface."""

from typing import Optional, List, Type, TypeVar, TYPE_CHECKING
import json
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
        self._debugger = LLMDebugger()

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

        instance = cls(gemini_model, model, temperature)

        # Warm up model with dummy call to avoid cold start on first real use
        instance.logger.info(f"Warming up {model}...")
        import asyncio
        try:
            asyncio.create_task(instance._warm_up())
        except Exception:
            pass  # Ignore warm-up failures

        return instance

    async def _warm_up(self) -> None:
        """Make a dummy API call to warm up the model and avoid cold start."""
        try:
            from webtask.llm import SystemMessage, TextContent
            dummy_messages = [
                SystemMessage(content=[TextContent(text="Hi")])
            ]
            gemini_content = messages_to_gemini_content(dummy_messages)
            await self.model.generate_content_async(
                gemini_content,
                generation_config=genai.GenerationConfig(temperature=0),
            )
            self.logger.info(f"{self.model_name} warmed up successfully")
        except Exception as e:
            self.logger.warning(f"Model warm-up failed: {e}")

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
        # Convert messages to Gemini format
        gemini_content = messages_to_gemini_content(messages)

        # Build tool declarations
        gemini_tools = build_tool_declarations(tools)

        # Create generation config
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
        )

        # Create tool config to allow text reasoning + function calling using protos
        # Mode.AUTO allows the model to decide whether to output text, call functions, or both
        tool_config = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(
                mode=protos.FunctionCallingConfig.Mode.AUTO,
            )
        )

        # Log request details
        import time
        num_messages = len(gemini_content)
        total_parts = sum(len(msg.get("parts", [])) for msg in gemini_content)
        num_tools = len(tools)
        self.logger.info(
            f"Calling Gemini API - Messages: {num_messages}, Parts: {total_parts}, Tools: {num_tools}"
        )

        # Call Gemini API with tools
        start_time = time.time()
        try:
            response = await self.model.generate_content_async(
                gemini_content,
                generation_config=generation_config,
                tools=[gemini_tools],
                tool_config=tool_config,
            )
            elapsed = time.time() - start_time
            self.logger.info(f"Gemini API responded in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Gemini API error after {elapsed:.2f}s: {type(e).__name__}: {e}")
            raise

        # Extract both text content (thoughts/reasoning) and tool calls from response
        tool_calls = []
        content_parts = []

        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                self.logger.debug(
                    f"Gemini returned {len(candidate.content.parts)} parts"
                )
                for i, part in enumerate(candidate.content.parts):
                    # Extract text content (thinking/reasoning)
                    if hasattr(part, "text") and part.text:
                        self.logger.debug(f"Part {i}: text ({len(part.text)} chars)")
                        content_parts.append(TextContent(text=part.text))

                    # Extract function calls
                    elif hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        self.logger.debug(f"Part {i}: function_call ({fc.name})")
                        tool_calls.append(
                            ToolCall(
                                name=fc.name,
                                arguments=dict(fc.args),
                            )
                        )

        # Create AssistantMessage with both content and tool_calls
        assistant_msg = AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None,
        )

        # Log what we extracted
        self.logger.debug(
            f"Created AssistantMessage: content={len(content_parts)} parts, "
            f"tool_calls={len(tool_calls)} calls"
        )

        # Save debug info if enabled
        self._debugger.save_call(messages, assistant_msg)

        return assistant_msg

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
        # Convert messages to Gemini format
        gemini_content = messages_to_gemini_content(messages)

        # Create generation config WITHOUT response_schema to avoid slow first call
        # We'll parse JSON ourselves instead
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            response_mime_type="application/json",
        )

        # Log request details
        import time
        num_messages = len(gemini_content)
        total_parts = sum(len(msg.get("parts", [])) for msg in gemini_content)
        self.logger.info(
            f"Calling Gemini API - Messages: {num_messages}, Parts: {total_parts}"
        )

        # Call Gemini API
        start_time = time.time()
        try:
            response = await self.model.generate_content_async(
                gemini_content,
                generation_config=generation_config,
            )
            elapsed = time.time() - start_time
            self.logger.info(f"Gemini API responded in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Gemini API error after {elapsed:.2f}s: {type(e).__name__}: {e}")
            raise

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
            result = response_model.model_validate(response_dict)

            # Save debug info if enabled (wrap text response in AssistantMessage)
            debug_response = AssistantMessage(content=[TextContent(text=text_response)])
            self._debugger.save_call(messages, debug_response)

            return result
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Failed to parse Gemini response as {response_model.__name__}: {e}"
            ) from e
