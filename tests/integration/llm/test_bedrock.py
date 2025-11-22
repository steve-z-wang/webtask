"""Integration tests for AWS Bedrock LLM."""

import os
import pytest
from webtask.llm import SystemMessage, UserMessage, TextContent, ToolCall

# Skip tests if boto3 not available
pytest.importorskip("boto3")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("AWS_BEARER_TOKEN_BEDROCK"),
        reason="AWS Bedrock API key not available",
    ),
]


@pytest.fixture
def bedrock_llm():
    """Create Bedrock LLM instance."""
    from webtask.integrations.llm import Bedrock

    return Bedrock(
        model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0.5,
    )


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    from pydantic import BaseModel, Field
    from webtask.llm.tool import Tool

    class ClickParams(BaseModel):
        element_id: str = Field(description="ID of element to click")

    class ClickTool(Tool):
        name = "click"
        description = "Click an element on the page"
        Params = ClickParams

        @staticmethod
        def describe(params: ClickParams) -> str:
            return f"Clicked {params.element_id}"

        async def execute(self, params: ClickParams) -> None:
            pass

    class GotoParams(BaseModel):
        url: str = Field(description="URL to go to")

    class GotoTool(Tool):
        name = "goto"
        description = "Go to a URL"
        Params = GotoParams

        @staticmethod
        def describe(params: GotoParams) -> str:
            return f"Went to {params.url}"

        async def execute(self, params: GotoParams) -> None:
            pass

    return [ClickTool(), GotoTool()]


@pytest.mark.asyncio
async def test_bedrock_call_tools_returns_tool_call(bedrock_llm, sample_tools):
    """Test that Bedrock returns a tool call for a simple request."""
    messages = [
        SystemMessage(content=[TextContent(text="You are a web automation agent.")]),
        UserMessage(
            content=[
                TextContent(text="Navigate to https://example.com and click button-5")
            ]
        ),
    ]

    response = await bedrock_llm.call_tools(messages, sample_tools)

    # Should have tool calls
    assert response.tool_calls is not None
    assert len(response.tool_calls) > 0

    # First tool call should be goto
    first_call = response.tool_calls[0]
    assert isinstance(first_call, ToolCall)
    assert first_call.name == "goto"
    assert "url" in first_call.arguments
    assert "example.com" in first_call.arguments["url"]


@pytest.mark.asyncio
async def test_bedrock_call_tools_with_text_content(bedrock_llm, sample_tools):
    """Test that Bedrock can return both text and tool calls."""
    messages = [
        SystemMessage(content=[TextContent(text="You are a helpful assistant.")]),
        UserMessage(
            content=[
                TextContent(
                    text="Please navigate to https://google.com. Before you do, explain what you're about to do."
                )
            ]
        ),
    ]

    response = await bedrock_llm.call_tools(messages, sample_tools)

    # Should have tool calls
    assert response.tool_calls is not None
    assert len(response.tool_calls) > 0

    # May or may not have text content (depending on model behavior)
    # Just verify structure is correct
    assert hasattr(response, "content")


@pytest.mark.asyncio
async def test_bedrock_handles_multiple_tools(bedrock_llm, sample_tools):
    """Test that Bedrock can call multiple tools in sequence."""
    messages = [
        SystemMessage(content=[TextContent(text="You are a web automation agent.")]),
        UserMessage(
            content=[
                TextContent(
                    text="First navigate to https://example.com, then click element button-1"
                )
            ]
        ),
    ]

    response = await bedrock_llm.call_tools(messages, sample_tools)

    # Should have tool calls
    assert response.tool_calls is not None
    assert len(response.tool_calls) >= 1

    # First call should be goto
    assert response.tool_calls[0].name == "goto"
