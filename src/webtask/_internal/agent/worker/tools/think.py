"""Worker meta tool - record reasoning."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class ThinkTool(Tool):
    """Record the worker's reasoning about next steps."""

    name = "think"
    description = "Record your reasoning about what to do next and why. Use this when you need to explain your thought process."

    class Params(BaseModel):
        """Parameters for think tool."""

        text: str = Field(description="Your reasoning about the next steps")

    async def execute(self, params: Params) -> str:
        """Record reasoning and return acknowledgment."""
        return "Noted"
