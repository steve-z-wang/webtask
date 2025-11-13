"""Tool registry for agent tools."""

import json
from typing import Dict, Any, List, TYPE_CHECKING
from webtask.agent.tool import Tool
from webtask._internal.llm import Block

if TYPE_CHECKING:
    from .tool_call import ProposedToolCall, ToolCall


class ToolRegistry:
    """Registry for managing and accessing agent tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        if not hasattr(tool, "name"):
            raise ValueError("Tool must have 'name' attribute")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
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

    def validate_proposed_tools(
        self, proposed_calls: List["ProposedToolCall"]
    ) -> List["ToolCall"]:
        """Validate proposed tools upfront, return ToolCall objects."""
        from .tool_call import ToolCall

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
        """Execute a tool call and return the result.

        Args:
            tool_call: ToolCall from LLM (with name, arguments, id fields)

        Returns:
            ToolResult with success or error status
        """
        from webtask.llm import ToolResult, ToolResultStatus

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

    def get_context(self) -> Block:
        """Get formatted context for LLM."""
        from .tool_call import ProposedToolCall

        # Get ProposedToolCall schema to show tool_call structure
        tool_call_schema = ProposedToolCall.model_json_schema()

        # Remove title for cleaner display
        tool_call_schema.pop("title", None)
        for prop in tool_call_schema.get("properties", {}).values():
            prop.pop("title", None)

        # Build tool schemas
        tool_schemas = []
        for tool in self.get_all():
            # Get Pydantic schema from tool.Params
            params_schema = tool.Params.model_json_schema()
            properties = params_schema.get("properties", {})
            required = params_schema.get("required", [])

            # Remove title from properties for cleaner schema
            for prop in properties.values():
                prop.pop("title", None)

            tool_schemas.append(
                {
                    "tool": tool.name,
                    "description": tool.description,
                    "parameters": properties,
                    "required": required,
                }
            )

        # Build complete schema
        complete_schema = {
            "tool_call_structure": tool_call_schema,
            "available_tools": tool_schemas,
        }

        return Block(
            heading="Available Tools", content=json.dumps(complete_schema, indent=2)
        )
