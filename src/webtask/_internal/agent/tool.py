"""Tool registry for agent tools."""

import logging
from typing import Dict, List, Tuple
from webtask.agent.tool import Tool
from webtask.llm import ToolResult, ToolResultStatus


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
        """Get all enabled tools."""
        return [tool for tool in self._tools.values() if tool.is_enabled()]

    def clear(self) -> None:
        """Clear all registered tools from the registry."""
        self._tools.clear()

    async def execute_tool_calls(
        self, tool_calls: List
    ) -> Tuple[List["ToolResult"], List[str]]:
        """Execute multiple tool calls in batch, stopping early if any tool fails or terminal tool succeeds."""
        results = []
        descriptions = []

        for tool_call in tool_calls:
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
                    )
                    results.append(result)
                    descriptions.append(f"{tool_call.name} (ERROR: Tool not found)")
                    break  # Stop on tool not found

                # Validate parameters and execute tool
                params = tool.Params(**tool_call.arguments)

                # Log tool execution start
                self._logger.info(
                    f"Executing tool: {tool_call.name} with params: {tool_call.arguments}"
                )

                # Execute tool and capture output
                await tool.execute(params)

                # Create success result
                result = ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    status=ToolResultStatus.SUCCESS,
                )
                results.append(result)

                description = tool.describe(params)
                descriptions.append(description)

                # Log tool execution success
                self._logger.info(f"Tool executed successfully: {description}")

                # If terminal tool succeeded, stop execution
                if tool.is_terminal:
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
                )
                results.append(result)
                descriptions.append(f"{tool_call.name} (ERROR: {error_msg})")
                break  # Stop on any error

        return results, descriptions
