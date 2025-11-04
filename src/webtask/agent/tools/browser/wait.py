"""Wait tool - pauses execution for specified duration."""

import asyncio
from typing import Type
from pydantic import Field
from ...schemas.params import ToolParams
from ...tool import Tool


class WaitParams(ToolParams):
    """Parameters for wait action."""

    seconds: float = Field(
        description="Seconds to wait (max 10)",
        ge=0.1,
        le=10.0,
    )


class WaitTool(Tool[WaitParams]):
    """Wait for a specified duration."""

    def __init__(self):
        """Initialize wait tool (no dependencies needed)."""
        pass

    @property
    def name(self) -> str:
        return "wait"

    @property
    def description(self) -> str:
        return "Wait for specified seconds (useful after actions that trigger page changes, modals, or dynamic content loading)"

    @property
    def params_class(self) -> Type[WaitParams]:
        return WaitParams

    async def execute(self, params: WaitParams):
        """Wait for the specified duration."""
        await asyncio.sleep(params.seconds)
