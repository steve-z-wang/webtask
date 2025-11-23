"""Google Gemini Computer Use LLM implementation for pixel-based browser control."""

from typing import Optional, List, TYPE_CHECKING

from google import genai
from google.genai import types

from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage, TextContent, ToolCall
from webtask._internal.utils.context_debugger import LLMContextDebugger
from .gemini_mapper import messages_to_gemini_content, clean_schema_for_gemini

if TYPE_CHECKING:
    from webtask.llm.tool import Tool

# Predefined Computer Use functions that we exclude (we use our own with descriptions)
EXCLUDED_PREDEFINED_FUNCTIONS = [
    "open_web_browser",
    "click_at",
    "hover_at",
    "type_text_at",
    "scroll_document",
    "scroll_at",
    "wait_5_seconds",
    "go_back",
    "go_forward",
    "search",
    "navigate",
    "key_combination",
    "drag_and_drop",
]


class GeminiComputerUse(LLM):
    """Google Gemini Computer Use implementation for pixel-based browser control.

    This uses the specialized gemini-2.5-computer-use model with custom tools
    that include description parameters for better logging and summaries.

    The model returns coordinates normalized to 0-999. The coordinate_scale
    attribute indicates this, and AgentBrowser uses it to scale coordinates
    to actual screen pixels.
    """

    # Model uses 0-999 normalized coordinates
    coordinate_scale = 1000

    def __init__(
        self,
        model: str = "gemini-2.5-computer-use-preview-10-2025",
        api_key: Optional[str] = None,
        temperature: float = 1.0,
    ):
        """Initialize GeminiComputerUse.

        Args:
            model: Computer Use model name
            api_key: Optional API key (if not set via environment variable)
            temperature: Sampling temperature (default 1.0 as recommended for Computer Use)
        """
        super().__init__()

        # Create client
        self._client = genai.Client(api_key=api_key) if api_key else genai.Client()

        self.model_name = model
        self.temperature = temperature
        self._debugger = LLMContextDebugger()

    def _build_tool_config(self, tools: List["Tool"]) -> List[types.Tool]:
        """Build Gemini tool configuration with Computer Use and custom functions."""
        # Build function declarations for our custom tools
        function_declarations = []
        for tool in tools:
            params_schema = tool.Params.model_json_schema()
            params_schema = clean_schema_for_gemini(params_schema)

            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=params_schema,
                )
            )

        return [
            # Computer Use tool with all predefined functions excluded
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=EXCLUDED_PREDEFINED_FUNCTIONS,
                ),
            ),
            # Our custom tools with descriptions
            types.Tool(function_declarations=function_declarations),
        ]

    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> AssistantMessage:
        """Generate response with tool calling.

        Note: Coordinates in returned tool calls are normalized (0-999).
        AgentBrowser handles scaling to actual screen pixels using coordinate_scale.
        """
        gemini_content, system_instruction = messages_to_gemini_content(messages)
        tool_configs = self._build_tool_config(tools)

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            system_instruction=system_instruction,
            tools=tool_configs,
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

        # Parse response
        assistant_msg = self._parse_response(response)
        self._debugger.save_call(messages, assistant_msg)
        return assistant_msg

    def _parse_response(self, response) -> AssistantMessage:
        """Parse Gemini response to AssistantMessage."""
        tool_calls = []
        content_parts = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                # Check for text content
                if hasattr(part, "text") and part.text:
                    content_parts.append(TextContent(text=part.text))
                # Check for function call
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    tool_calls.append(ToolCall(name=fc.name, arguments=args))

        return AssistantMessage(
            content=content_parts if content_parts else None,
            tool_calls=tool_calls if tool_calls else None,
        )
