"""Mappers for transforming between webtask and AWS Bedrock formats."""

import base64
from typing import Any, Dict, List, TYPE_CHECKING
from webtask.llm import (
    Role,
    Message,
    Text,
    Image,
    ToolCall,
    ToolResult,
)
from webtask._internal.llm.json_schema_utils import resolve_json_schema_refs

if TYPE_CHECKING:
    from webtask.llm.tool import Tool


def messages_to_bedrock_format(
    messages: List[Message],
) -> tuple[List[Dict[str, Any]], str | None]:
    """
    Convert Message history to Bedrock Converse API format.

    Returns:
        Tuple of (messages list, system_prompt string or None)
    """
    bedrock_messages = []
    system_prompt = None

    for msg in messages:
        if msg.role == Role.SYSTEM:
            # Extract system prompt (Bedrock uses separate system parameter)
            if msg.content:
                texts = [c.text for c in msg.content if isinstance(c, Text)]
                system_prompt = "\n\n".join(texts)

        elif msg.role == Role.USER:
            # Build content list (text and images)
            content = []

            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, Text):
                        content.append({"text": content_part.text})
                    elif isinstance(content_part, Image):
                        # Bedrock expects base64 encoded images
                        content.append(
                            {
                                "image": {
                                    "format": "png",  # Assume PNG, could be made configurable
                                    "source": {
                                        "bytes": base64.b64decode(content_part.data)
                                    },
                                }
                            }
                        )

            if content:
                bedrock_messages.append({"role": "user", "content": content})

        elif msg.role == Role.MODEL:
            # Model message with optional tool calls
            content = []

            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, Text):
                        content.append({"text": content_part.text})
                    elif isinstance(content_part, ToolCall):
                        content.append(
                            {
                                "toolUse": {
                                    "toolUseId": content_part.id
                                    or f"call-{content_part.name}",
                                    "name": content_part.name,
                                    "input": content_part.arguments,
                                }
                            }
                        )

            if content:
                bedrock_messages.append({"role": "assistant", "content": content})

        elif msg.role == Role.TOOL:
            # Tool results message - convert to Bedrock tool result format
            content = []

            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, ToolResult):
                        # Create tool result
                        tool_result_content = {
                            "toolUseId": content_part.tool_call_id,
                            "content": [],
                        }

                        if content_part.error:
                            tool_result_content["status"] = "error"
                            tool_result_content["content"].append(
                                {"text": f"Error: {content_part.error}"}
                            )
                        else:
                            # Bedrock doesn't have an explicit success status, omit status for success
                            tool_result_content["content"].append(
                                {"text": f"Status: {content_part.status.value}"}
                            )

                        content.append({"toolResult": tool_result_content})
                    elif isinstance(content_part, Text):
                        content.append({"text": content_part.text})
                    elif isinstance(content_part, Image):
                        content.append(
                            {
                                "image": {
                                    "format": "png",
                                    "source": {
                                        "bytes": base64.b64decode(content_part.data)
                                    },
                                }
                            }
                        )

            if content:
                bedrock_messages.append({"role": "user", "content": content})

    return bedrock_messages, system_prompt


def build_tool_config(tools: List["Tool"]) -> Dict[str, Any]:
    """Build Bedrock tool configuration from tools."""
    tool_specs = []

    for tool in tools:
        # Convert Pydantic model to JSON schema
        params_schema = tool.Params.model_json_schema()

        # Resolve $ref references (Bedrock doesn't support $ref)
        params_schema = resolve_json_schema_refs(params_schema)

        # Build input schema (Bedrock format)
        input_schema = {
            "json": {
                "type": "object",
                "properties": params_schema.get("properties", {}),
                "required": params_schema.get("required", []),
            }
        }

        tool_specs.append(
            {
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": input_schema,
                }
            }
        )

    return {"tools": tool_specs}


def bedrock_response_to_message(response: Dict[str, Any]) -> Message:
    """Convert Bedrock Converse API response to Message with Role.MODEL."""
    content = []

    # Extract content from response
    if "output" in response and "message" in response["output"]:
        message_content = response["output"]["message"].get("content", [])

        for content_block in message_content:
            if "text" in content_block:
                content.append(Text(text=content_block["text"]))
            elif "toolUse" in content_block:
                tool_use = content_block["toolUse"]
                content.append(
                    ToolCall(
                        id=tool_use["toolUseId"],
                        name=tool_use["name"],
                        arguments=tool_use["input"],
                    )
                )

    return Message(
        role=Role.MODEL,
        content=content if content else None,
    )
