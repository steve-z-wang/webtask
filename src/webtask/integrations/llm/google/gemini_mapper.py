"""Mappers for transforming between webtask and Gemini formats."""

import base64
import io
from typing import Any, Dict, List, TYPE_CHECKING
from PIL import Image as PILImage
from google.generativeai import types, protos
from webtask.llm import (
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


def messages_to_gemini_content(messages: List[Message]) -> List[types.ContentDict]:
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

            # Add tool calls as function call parts
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    parts.append(
                        protos.Part(
                            function_call=protos.FunctionCall(
                                name=tool_call.name, args=tool_call.arguments
                            )
                        )
                    )

            gemini_messages.append({"role": "model", "parts": parts})

        elif isinstance(msg, ToolResultMessage):
            # Tool results message - convert to Gemini function response
            parts = []

            for result in msg.results:
                # Create function response for each tool result
                response_data = {"status": result.status.value}
                if result.error:
                    response_data["error"] = result.error

                parts.append(
                    protos.Part(
                        function_response=protos.FunctionResponse(
                            name=result.name, response=response_data
                        )
                    )
                )

            # Add observation content (DOM + screenshot) as text/images
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


def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
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
                    prop_name: clean_schema_for_gemini(prop_schema)
                    for prop_name, prop_schema in value.items()
                }
            elif key == "items" and isinstance(value, dict):
                # Recursively clean array items schema
                cleaned[key] = clean_schema_for_gemini(value)
            else:
                cleaned[key] = value

    return cleaned


def convert_gemini_types(value: Any) -> Any:
    """
    Recursively convert Gemini-specific types to standard Python types.

    Converts:
    - MapComposite → dict
    - RepeatedComposite → list
    - Nested structures recursively
    - Primitives (str, int, float, bool, None) remain as-is

    Args:
        value: Value to convert (may be MapComposite, RepeatedComposite, dict, list, or primitive)

    Returns:
        Standard Python type (dict, list, or primitive)
    """
    # Check if it's a MapComposite (dict-like Gemini type)
    if (
        hasattr(value, "__iter__")
        and hasattr(value, "keys")
        and not isinstance(value, (str, bytes))
    ):
        # Convert to dict and recursively convert all values
        return {k: convert_gemini_types(v) for k, v in dict(value).items()}

    # Check if it's a RepeatedComposite or list
    elif isinstance(value, (list, tuple)) or (
        hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict))
    ):
        # Convert to list and recursively convert all items
        try:
            return [convert_gemini_types(item) for item in value]
        except TypeError:
            # Not iterable in the way we expect, return as-is
            return value

    # Primitives (str, int, float, bool, None) - return as-is
    else:
        return value


def build_tool_declarations(tools: List["Tool"]) -> types.Tool:
    """Build Gemini function declarations from tools."""
    function_declarations = []

    for tool in tools:
        # Convert Pydantic model to JSON schema
        params_schema = tool.Params.model_json_schema()

        # Clean schema to be Gemini-compatible
        params_schema = clean_schema_for_gemini(params_schema)

        function_declarations.append(
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=params_schema,
            )
        )

    return types.Tool(function_declarations=function_declarations)


def gemini_response_to_assistant_message(response) -> "AssistantMessage":
    """Convert Gemini response to AssistantMessage."""
    tool_calls = []
    content_parts = []

    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                content_parts.append(TextContent(text=part.text))
            elif hasattr(part, "function_call") and part.function_call:
                # Convert arguments recursively to handle nested MapComposite/RepeatedComposite
                tool_calls.append(
                    ToolCall(
                        name=part.function_call.name,
                        arguments=convert_gemini_types(part.function_call.args),
                    )
                )

    return AssistantMessage(
        content=content_parts if content_parts else None,
        tool_calls=tool_calls if tool_calls else None,
    )
