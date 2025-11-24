"""Mappers for transforming between webtask and Gemini formats (google-genai SDK)."""

import base64
from typing import Any, Dict, List, TYPE_CHECKING

from google.genai import types

from dodo import (
    Message,
    SystemMessage,
    UserMessage,
    ModelMessage,
    Text,
    Image,
    ToolResult,
)
from dodo.llm.message import ToolCall
from webtask._internal.llm.json_schema_utils import resolve_json_schema_refs

if TYPE_CHECKING:
    from dodo import Tool


def messages_to_gemini_content(
    messages: List[Message],
) -> tuple[List[types.Content], str | None]:
    """
    Convert Message history to Gemini's content format.

    Gemini uses alternating user/model roles. System messages are
    extracted separately for use with GenerateContentConfig.system_instruction.

    Returns:
        Tuple of (gemini_contents, system_instruction)
    """
    gemini_messages = []
    system_instruction = None

    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Extract system instruction (to be passed to config separately)
            if msg.content:
                system_instruction = "\n\n".join([part.text for part in msg.content])

        elif isinstance(msg, UserMessage):
            # Build parts list (text, images, and tool results)
            parts = []

            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, ToolResult):
                        # Convert ToolResult to Gemini function response
                        response_data = {"status": content_part.status.value}
                        if content_part.error:
                            response_data["error"] = content_part.error
                        parts.append(
                            types.Part.from_function_response(
                                name=content_part.name,
                                response=response_data,
                            )
                        )
                    elif isinstance(content_part, Text):
                        parts.append(types.Part.from_text(text=content_part.text))
                    elif isinstance(content_part, Image):
                        # Convert base64 to inline data
                        parts.append(
                            types.Part.from_bytes(
                                data=base64.b64decode(content_part.base64),
                                mime_type=content_part.mime_type.value,
                            )
                        )

            # Only add message if parts is not empty (Gemini requires at least one part)
            if parts:
                gemini_messages.append(types.Content(role="user", parts=parts))

        elif isinstance(msg, ModelMessage):
            # Assistant message with tool calls
            parts = []

            # Include content if present
            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, Text):
                        parts.append(types.Part.from_text(text=content_part.text))
                    elif isinstance(content_part, Image):
                        parts.append(
                            types.Part.from_bytes(
                                data=base64.b64decode(content_part.base64),
                                mime_type=content_part.mime_type.value,
                            )
                        )

            # Add tool calls as function call parts
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    parts.append(
                        types.Part.from_function_call(
                            name=tool_call.name,
                            args=tool_call.arguments,
                        )
                    )

            # Only add message if parts is not empty (Gemini requires at least one part)
            if parts:
                gemini_messages.append(types.Content(role="model", parts=parts))

    return gemini_messages, system_instruction


def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean Pydantic JSON schema to be compatible with Gemini.

    Gemini only accepts a subset of JSON schema fields and doesn't support $ref.
    This function resolves $ref references and removes unsupported fields.

    Args:
        schema: The schema to clean

    Returns:
        Cleaned schema compatible with Gemini
    """
    # First resolve all $ref references using shared utility
    schema = resolve_json_schema_refs(schema)

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
        elif key == "anyOf":
            # Handle anyOf (used for Optional types)
            # Filter out null type and use the first non-null type
            if isinstance(value, list):
                non_null_schemas = [s for s in value if s.get("type") != "null"]
                if non_null_schemas:
                    # Use the first non-null schema (recursively clean it)
                    non_null_schema = clean_schema_for_gemini(non_null_schemas[0])
                    # Merge the non-null schema into cleaned (flattening anyOf)
                    cleaned.update(non_null_schema)
                    # Mark as nullable if there was a null option
                    if len(value) > len(non_null_schemas):
                        cleaned["nullable"] = True

    return cleaned


def build_tool_config(tools: List["Tool"]) -> types.Tool:
    """Build Gemini Tool with function declarations from tools."""
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


def gemini_response_to_model_message(response) -> "ModelMessage":
    """Convert Gemini response to ModelMessage."""
    tool_calls = []
    content_parts = []

    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            # Check for text content
            if hasattr(part, "text") and part.text:
                content_parts.append(Text(text=part.text))
            # Check for function call
            elif hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                # Convert args to dict - in new SDK args is already a dict-like object
                args = dict(fc.args) if fc.args else {}
                tool_calls.append(
                    ToolCall(
                        name=fc.name,
                        arguments=args,
                    )
                )

    return ModelMessage(
        content=content_parts if content_parts else None,
        tool_calls=tool_calls if tool_calls else None,
    )
