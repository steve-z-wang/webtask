"""Tool registry for agent tools."""

from typing import Dict, List, Tuple, TYPE_CHECKING
from webtask.agent.tool import Tool
from webtask.llm import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from .tool_call import ProposedToolCall, ToolCall


class ToolRegistry:
    """Registry for managing and accessing agent tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry. Replaces existing tool if name already exists."""
        if not hasattr(tool, "name"):
            raise ValueError("Tool must have 'name' attribute")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def get_all(self) -> List[Tool]:
        """Get all enabled tools."""
        return [tool for tool in self._tools.values() if tool.is_enabled()]

    def clear(self) -> None:
        """Clear all registered tools from the registry."""
        self._tools.clear()

    def validate_proposed_tools(
        self, proposed_calls: List["ProposedToolCall"]
    ) -> List["ToolCall"]:
        """Validate proposed tools upfront, return ToolCall objects."""

        tool_calls = []
        for proposed in proposed_calls:
            tool_call = ToolCall.from_proposed(proposed)
            try:
                tool = self.get(tool_call.tool)
                # Validate by instantiating Params
                tool.Params(**tool_call.parameters)
            except Exception as e:
                tool_call.mark_failure(f"Validation error: {e}")
            tool_calls.append(tool_call)
        return tool_calls

    async def execute_tool_call(self, tool_call) -> "ToolResult":
        """Execute a tool call and return the result."""
        try:
            # Get tool and validate parameters
            tool = self.get(tool_call.name)
            params = tool.Params(**tool_call.arguments)

            # Execute tool and capture output
            output = await tool.execute(params)

            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolResultStatus.SUCCESS,
                output=output,
            )

        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolResultStatus.ERROR,
                error=str(e),
            )

    async def execute_tool_calls(
        self, tool_calls: List
    ) -> Tuple[List["ToolResult"], List[str]]:
        """Execute multiple tool calls in batch, stopping early if terminal tool succeeds."""
        results = []
        descriptions = []

        for tool_call in tool_calls:
            # Get tool and generate description
            tool = self.get(tool_call.name)
            params = tool.Params(**tool_call.arguments)
            description = tool.describe(params)

            # Execute tool
            result = await self.execute_tool_call(tool_call)
            results.append(result)

            # Add error to description if failed
            if result.status == ToolResultStatus.ERROR:
                descriptions.append(f"{description} (ERROR: {result.error})")
            else:
                descriptions.append(description)

            # If terminal tool succeeded, stop execution
            if result.status == ToolResultStatus.SUCCESS and tool.is_terminal:
                break

        return results, descriptions
