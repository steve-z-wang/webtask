"""Tool registry for agent tools."""

import logging
from typing import Dict, List
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus


class ToolRegistry:
    """Registry for managing and accessing agent tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._logger = logging.getLogger(__name__)

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
        """Get all registered tools."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Clear all registered tools from the registry."""
        self._tools.clear()

    async def execute_tool_calls(self, tool_calls: List) -> List[ToolResult]:
        """Execute multiple tool calls in batch, stopping early if any tool fails or is terminal."""
        results = []
        executed_count = 0

        for idx, tool_call in enumerate(tool_calls):
            try:
                # Get tool - catch KeyError separately for clearer error message
                try:
                    tool = self.get(tool_call.name)
                except KeyError:
                    error_msg = f"Tool '{tool_call.name}' not found in registry"
                    self._logger.error(error_msg)
                    result = ToolResult(
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                        status=ToolResultStatus.ERROR,
                        error=error_msg,
                        description=f"{tool_call.name} (ERROR: Tool not found)",
                    )
                    results.append(result)
                    executed_count = idx + 1
                    break  # Stop on tool not found

                # Validate parameters
                params = tool.Params(**tool_call.arguments)

                # Log tool execution start
                self._logger.info(
                    f"Executing tool: {tool_call.name} with params: {tool_call.arguments}"
                )

                # Execute tool and get result
                result = await tool.execute(params)
                result.tool_call_id = tool_call.id
                results.append(result)
                executed_count = idx + 1

                # Log tool execution success
                self._logger.info(f"Tool executed successfully: {result.description}")

                # If terminal tool succeeded or error occurred, stop execution
                if result.terminal or result.status == ToolResultStatus.ERROR:
                    break

            except Exception as e:
                # Params validation or tool execution error
                error_msg = str(e)
                self._logger.error(
                    f"Tool execution failed: {tool_call.name} - {error_msg}"
                )
                result = ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    status=ToolResultStatus.ERROR,
                    error=error_msg,
                    description=f"{tool_call.name} (ERROR: {error_msg})",
                )
                results.append(result)
                executed_count = idx + 1
                break  # Stop on any error

        # Create skipped results for remaining tool calls (required for Bedrock compatibility)
        for tool_call in tool_calls[executed_count:]:
            result = ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolResultStatus.ERROR,
                error="Skipped due to previous tool failure or terminal action",
                description=f"{tool_call.name} (SKIPPED)",
            )
            results.append(result)
            self._logger.info(
                f"Tool skipped: {tool_call.name} (previous tool failed or terminal)"
            )

        return results
