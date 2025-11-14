"""Worker meta tool - record observation."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class ObserveTool(Tool):
    """Record what the worker observes on the page."""

    name = "observe"
    description = "Record what you observe on the page (UI state, messages, errors). Use this when you need to note important observations."

    class Params(BaseModel):
        """Parameters for observe tool."""

        text: str = Field(description="Your observation of the current page state")

    async def execute(self, params: Params) -> str:
        """Record observation and return acknowledgment."""
        return "Noted"
