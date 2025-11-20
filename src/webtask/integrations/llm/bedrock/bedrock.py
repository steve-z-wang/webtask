"""AWS Bedrock LLM implementation using Converse API."""

from typing import Optional, List, TYPE_CHECKING

from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage
from webtask._internal.utils.context_debugger import LLMContextDebugger
from .bedrock_mapper import (
    messages_to_bedrock_format,
    build_tool_config,
    bedrock_response_to_assistant_message,
)

try:
    import boto3
except ImportError:
    raise ImportError(
        "boto3 is required for Bedrock integration. "
        "Install it with: pip install boto3"
    )

if TYPE_CHECKING:
    from webtask.llm.tool import Tool


class Bedrock(LLM):
    """AWS Bedrock implementation using Converse API.

    Supports Claude models via AWS Bedrock.
    """

    def __init__(
        self,
        model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ):
        """Initialize Bedrock.

        Args:
            model: Bedrock model ID (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")
            region_name: AWS region name (default: "us-east-1")
            aws_access_key_id: Optional AWS access key (if not using default credentials)
            aws_secret_access_key: Optional AWS secret key
            aws_session_token: Optional AWS session token
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        super().__init__()

        # Initialize boto3 client
        session_kwargs = {"region_name": region_name}
        if aws_access_key_id:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            session_kwargs["aws_session_token"] = aws_session_token

        self.client = boto3.client("bedrock-runtime", **session_kwargs)
        self.model_id = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._debugger = LLMContextDebugger()

    async def call_tools(
        self,
        messages: List[Message],
        tools: List["Tool"],
    ) -> AssistantMessage:
        """Generate response with tool calling."""
        bedrock_messages, system_prompt = messages_to_bedrock_format(messages)
        tool_config = build_tool_config(tools)

        # Build inference configuration
        inference_config = {
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }

        # Prepare converse request
        request_params = {
            "modelId": self.model_id,
            "messages": bedrock_messages,
            "inferenceConfig": inference_config,
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]

        if tool_config:
            request_params["toolConfig"] = tool_config

        # Call Bedrock Converse API
        response = self.client.converse(**request_params)

        # Log token usage
        if "usage" in response:
            usage = response["usage"]
            self.logger.info(
                f"Token usage - Input: {usage.get('inputTokens', 0)}, "
                f"Output: {usage.get('outputTokens', 0)}, "
                f"Total: {usage.get('totalTokens', 0)}"
            )

        assistant_msg = bedrock_response_to_assistant_message(response)
        self._debugger.save_call(messages, assistant_msg)
        return assistant_msg
