"""Wait tool - pauses execution for specified duration."""

import asyncio
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


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

    async def execute(self, params: Params) -> None:
        """Wait for the specified duration."""
        await asyncio.sleep(params.seconds)
