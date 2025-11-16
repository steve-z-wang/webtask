"""Converters for transforming between webtask and Gemini formats."""

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


def tool_calls_from_gemini_response(candidate) -> List[ToolCall]:
    """Extract tool calls from Gemini response candidate."""
    tool_calls = []

    if candidate.content and candidate.content.parts:
        for part in candidate.content.parts:
            # Check if this part contains a function call
            if part.function_call:
                fc = part.function_call
                # Convert Gemini function call to our ToolCall format
                tool_calls.append(
                    ToolCall(
                        id=fc.name,  # Gemini doesn't provide IDs, use name
                        name=fc.name,
                        arguments=dict(fc.args),
                    )
                )

    return tool_calls
