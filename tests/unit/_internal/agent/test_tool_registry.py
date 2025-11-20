"""Tests for ToolRegistry error handling."""

import pytest
from pydantic import BaseModel, Field
from webtask.llm.tool import Tool
from webtask.llm import ToolCall, ToolResultStatus
from webtask._internal.agent.tool_registry import ToolRegistry

pytestmark = pytest.mark.unit


# Test fixtures
class DummyParams(BaseModel):
    """Parameters for dummy tool."""

    value: str = Field(description="A required string value")
    count: int = Field(default=1, description="An optional count")


class DummyTool(Tool):
    """Simple tool for testing."""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def description(self) -> str:
        return "A dummy tool for testing"

    @property
    def Params(self):
        return DummyParams

    @staticmethod
    def describe(params: DummyParams) -> str:
        """Generate description."""
        return f"Dummy action with value={params.value}"

    async def execute(self, params: DummyParams) -> str:
        """Execute dummy action."""
        return f"Executed with {params.value} x{params.count}"


@pytest.fixture
def registry():
    """Create a tool registry with a dummy tool."""
    reg = ToolRegistry()
    reg.register(DummyTool())
    return reg


@pytest.mark.asyncio
async def test_execute_nonexistent_tool(registry):
    """Test calling a tool that doesn't exist."""
    # Create a tool call for a non-existent tool
    tool_call = ToolCall(
        id="test-1",
        name="scroll",  # This tool doesn't exist
        arguments={"direction": "down"},
    )

    # Execute and check result
    results, descriptions = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "scroll"
    assert "not found in registry" in results[0].error

    # Should have error description
    assert len(descriptions) == 1
    assert "ERROR" in descriptions[0]
    assert "Tool not found" in descriptions[0]


@pytest.mark.asyncio
async def test_execute_tool_with_invalid_params(registry):
    """Test calling a tool with wrong parameters."""
    # Create a tool call with invalid params (missing required 'value' field)
    tool_call = ToolCall(
        id="test-2",
        name="dummy",
        arguments={"count": 5},  # Missing required 'value' field
    )

    # Execute and check result
    results, descriptions = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    assert results[0].error is not None  # Should contain validation error

    # Should have error description
    assert len(descriptions) == 1
    assert "ERROR" in descriptions[0]


@pytest.mark.asyncio
async def test_execute_tool_with_wrong_param_type(registry):
    """Test calling a tool with wrong parameter type."""
    # Create a tool call with wrong type (count should be int, not string)
    tool_call = ToolCall(
        id="test-3",
        name="dummy",
        arguments={"value": "test", "count": "not-a-number"},
    )

    # Execute and check result
    results, descriptions = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    assert results[0].error is not None

    # Should have error description
    assert len(descriptions) == 1
    assert "ERROR" in descriptions[0]


@pytest.mark.asyncio
async def test_execute_valid_tool_call(registry):
    """Test successful tool execution."""
    # Create a valid tool call
    tool_call = ToolCall(
        id="test-4", name="dummy", arguments={"value": "hello", "count": 3}
    )

    # Execute and check result
    results, descriptions = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with SUCCESS status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.SUCCESS
    assert results[0].name == "dummy"
    assert results[0].error is None

    # Should have success description
    assert len(descriptions) == 1
    assert "ERROR" not in descriptions[0]
    assert "value=hello" in descriptions[0]


@pytest.mark.asyncio
async def test_stop_on_first_error(registry):
    """Test that execution stops on first error."""
    # Create multiple tool calls where the first one fails
    tool_calls = [
        ToolCall(id="test-5", name="nonexistent", arguments={}),
        ToolCall(id="test-6", name="dummy", arguments={"value": "test"}),
    ]

    # Execute
    results, descriptions = await registry.execute_tool_calls(tool_calls)

    # Should have 2 results (1 executed with error + 1 skipped)
    assert len(results) == 2
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "nonexistent"
    assert "not found" in results[0].error

    # Second tool should be skipped
    assert results[1].status == ToolResultStatus.ERROR
    assert results[1].name == "dummy"
    assert "Skipped" in results[1].error

    # Should have 2 descriptions
    assert len(descriptions) == 2
    assert "ERROR" in descriptions[0]
    assert "SKIPPED" in descriptions[1]


@pytest.mark.asyncio
async def test_stop_on_param_validation_error(registry):
    """Test that execution stops on parameter validation error."""
    # Create multiple tool calls where the first has invalid params
    tool_calls = [
        ToolCall(id="test-7", name="dummy", arguments={"count": 1}),  # Missing value
        ToolCall(id="test-8", name="dummy", arguments={"value": "test"}),
    ]

    # Execute
    results, descriptions = await registry.execute_tool_calls(tool_calls)

    # Should have 2 results (1 executed with error + 1 skipped)
    assert len(results) == 2
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    assert "validation error" in results[0].error

    # Second tool should be skipped
    assert results[1].status == ToolResultStatus.ERROR
    assert results[1].name == "dummy"
    assert "Skipped" in results[1].error

    # Should have 2 descriptions
    assert len(descriptions) == 2
    assert "ERROR" in descriptions[0]
    assert "SKIPPED" in descriptions[1]
