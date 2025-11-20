"""Mappers for transforming between webtask and AWS Bedrock formats."""

import base64
from typing import Any, Dict, List, TYPE_CHECKING
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
        if isinstance(msg, SystemMessage):
            # Extract system prompt (Bedrock uses separate system parameter)
            if msg.content:
                system_prompt = "\n\n".join([part.text for part in msg.content])

        elif isinstance(msg, UserMessage):
            # Build content list (text and images)
            content = []

            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, TextContent):
                        content.append({"text": content_part.text})
                    elif isinstance(content_part, ImageContent):
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

        elif isinstance(msg, AssistantMessage):
            # Assistant message with optional tool calls
            content = []

            # Include text content if present
            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, TextContent):
                        content.append({"text": content_part.text})

            # Add tool calls
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    content.append(
                        {
                            "toolUse": {
                                "toolUseId": tool_call.id or f"call-{tool_call.name}",
                                "name": tool_call.name,
                                "input": tool_call.arguments,
                            }
                        }
                    )

            if content:
                bedrock_messages.append({"role": "assistant", "content": content})

        elif isinstance(msg, ToolResultMessage):
            # Tool results message - convert to Bedrock tool result format
            content = []

            for result in msg.results:
                # Create tool result
                tool_result_content = {"toolUseId": result.id, "content": []}

                if result.error:
                    tool_result_content["status"] = "error"
                    tool_result_content["content"].append(
                        {"text": f"Error: {result.error}"}
                    )
                else:
                    # Bedrock doesn't have an explicit success status, omit status for success
                    tool_result_content["content"].append(
                        {"text": f"Status: {result.status.value}"}
                    )

                content.append({"toolResult": tool_result_content})

            # Add observation content (DOM + screenshot) as additional content
            if msg.content:
                for content_part in msg.content:
                    if isinstance(content_part, TextContent):
                        content.append({"text": content_part.text})
                    elif isinstance(content_part, ImageContent):
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


def bedrock_response_to_assistant_message(response: Dict[str, Any]) -> AssistantMessage:
    """Convert Bedrock Converse API response to AssistantMessage."""
    tool_calls = []
    content_parts = []

    # Extract content from response
    if "output" in response and "message" in response["output"]:
        message_content = response["output"]["message"].get("content", [])

        for content_block in message_content:
            if "text" in content_block:
                content_parts.append(TextContent(text=content_block["text"]))
            elif "toolUse" in content_block:
                tool_use = content_block["toolUse"]
                tool_calls.append(
                    ToolCall(
                        id=tool_use["toolUseId"],
                        name=tool_use["name"],
                        arguments=tool_use["input"],
                    )
                )

    return AssistantMessage(
        content=content_parts if content_parts else None,
        tool_calls=tool_calls if tool_calls else None,
    )
