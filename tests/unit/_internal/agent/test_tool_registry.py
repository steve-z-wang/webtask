"""Tests for ToolRegistry error handling."""

import pytest
from pydantic import BaseModel, Field
from webtask.llm.tool import Tool, ToolParams
from webtask.llm import ToolCall, ToolResultStatus
from webtask.llm.message import ToolResult
from webtask._internal.agent.tool_registry import ToolRegistry

pytestmark = pytest.mark.unit


# Test fixtures
class DummyParams(BaseModel):
    """Parameters for dummy tool."""

    value: str = Field(description="A required string value")
    count: int = Field(default=1, description="An optional count")


class DummyTool(Tool):
    """Simple tool for testing."""

    name = "dummy"
    description = "A dummy tool for testing"
    Params = DummyParams

    async def execute(self, params: DummyParams) -> ToolResult:
        """Execute dummy action."""
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Dummy action with value={params.value}",
        )


class StrictTool(Tool):
    """Tool using ToolParams base class that forbids extra fields."""

    name = "strict"
    description = "A strict tool that rejects extra parameters"

    class Params(ToolParams):
        """Parameters for strict tool."""

        text: str = Field(description="Text to process")

    async def execute(self, params: Params) -> ToolResult:
        """Execute strict action."""
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Processed: {params.text}",
        )


@pytest.fixture
def registry():
    """Create a tool registry with a dummy tool."""
    reg = ToolRegistry()
    reg.register(DummyTool())
    return reg


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_nonexistent_tool(registry):
    """Test calling a tool that doesn't exist."""
    # Create a tool call for a non-existent tool
    tool_call = ToolCall(
        id="test-1",
        name="scroll",  # This tool doesn't exist
        arguments={"direction": "down"},
    )

    # Execute and check result
    results = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "scroll"
    assert "not found in registry" in results[0].error

    # Description should contain error info
    assert "ERROR" in results[0].description
    assert "Tool not found" in results[0].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_tool_with_invalid_params(registry):
    """Test calling a tool with wrong parameters."""
    # Create a tool call with invalid params (missing required 'value' field)
    tool_call = ToolCall(
        id="test-2",
        name="dummy",
        arguments={"count": 5},  # Missing required 'value' field
    )

    # Execute and check result
    results = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    assert results[0].error is not None  # Should contain validation error

    # Description should contain error info
    assert "ERROR" in results[0].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_tool_with_wrong_param_type(registry):
    """Test calling a tool with wrong parameter type."""
    # Create a tool call with wrong type (count should be int, not string)
    tool_call = ToolCall(
        id="test-3",
        name="dummy",
        arguments={"value": "test", "count": "not-a-number"},
    )

    # Execute and check result
    results = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    assert results[0].error is not None

    # Description should contain error info
    assert "ERROR" in results[0].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_execute_valid_tool_call(registry):
    """Test successful tool execution."""
    # Create a valid tool call
    tool_call = ToolCall(
        id="test-4", name="dummy", arguments={"value": "hello", "count": 3}
    )

    # Execute and check result
    results = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with SUCCESS status
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.SUCCESS
    assert results[0].name == "dummy"
    assert results[0].error is None

    # Description should contain the action info
    assert "ERROR" not in results[0].description
    assert "value=hello" in results[0].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_on_first_error(registry):
    """Test that execution stops on first error."""
    # Create multiple tool calls where the first one fails
    tool_calls = [
        ToolCall(id="test-5", name="nonexistent", arguments={}),
        ToolCall(id="test-6", name="dummy", arguments={"value": "test"}),
    ]

    # Execute
    results = await registry.execute_tool_calls(tool_calls)

    # Should have 2 results (1 executed with error + 1 skipped)
    assert len(results) == 2
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "nonexistent"
    assert "not found" in results[0].error

    # Second tool should be skipped
    assert results[1].status == ToolResultStatus.ERROR
    assert results[1].name == "dummy"
    assert "Skipped" in results[1].error

    # Descriptions should reflect status
    assert "ERROR" in results[0].description
    assert "SKIPPED" in results[1].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stop_on_param_validation_error(registry):
    """Test that execution stops on parameter validation error."""
    # Create multiple tool calls where the first has invalid params
    tool_calls = [
        ToolCall(id="test-7", name="dummy", arguments={"count": 1}),  # Missing value
        ToolCall(id="test-8", name="dummy", arguments={"value": "test"}),
    ]

    # Execute
    results = await registry.execute_tool_calls(tool_calls)

    # Should have 2 results (1 executed with error + 1 skipped)
    assert len(results) == 2
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "dummy"
    # Note: pydantic validation errors may format differently
    assert results[0].error is not None

    # Second tool should be skipped
    assert results[1].status == ToolResultStatus.ERROR
    assert results[1].name == "dummy"
    assert "Skipped" in results[1].error

    # Descriptions should reflect status
    assert "ERROR" in results[0].description
    assert "SKIPPED" in results[1].description


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tool_params_rejects_extra_fields():
    """Test that ToolParams base class rejects extra fields."""
    # Create a registry with the strict tool
    registry = ToolRegistry()
    registry.register(StrictTool())

    # Create a tool call with extra parameters that shouldn't be accepted
    tool_call = ToolCall(
        id="test-extra",
        name="strict",
        arguments={"text": "hello", "element_id": "input-5"},  # element_id is extra
    )

    # Execute and check result
    results = await registry.execute_tool_calls([tool_call])

    # Should have 1 result with ERROR status due to extra field
    assert len(results) == 1
    assert results[0].status == ToolResultStatus.ERROR
    assert results[0].name == "strict"
    assert results[0].error is not None
    assert "extra" in results[0].error.lower() or "element_id" in results[0].error
