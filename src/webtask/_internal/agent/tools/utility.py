"""Utility tools for common actions."""

from pydantic import BaseModel, Field
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus
from webtask._internal.utils.wait import wait


class WaitTool(Tool):
    """Wait for a specified duration."""

    name = "wait"
    description = "Wait for specified seconds (useful after actions that trigger page changes, modals, or dynamic content loading)"

    class Params(BaseModel):
        """Parameters for wait tool."""

        seconds: float = Field(
            description="Seconds to wait (max 10)",
            ge=0.1,
            le=10.0,
        )

    async def execute(self, params: Params) -> ToolResult:
        """Wait for the specified duration."""
        await wait(params.seconds)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Waited {params.seconds} seconds",
        )
