"""Verifier tool - request correction."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class RequestCorrectionTool(Tool):
    """Request Worker to retry with feedback."""

    name = "request_correction"
    description = "Request Worker to retry the task with feedback to fix issues (use for small, fixable mistakes like wrong element clicked or typo)"

    class Params(BaseModel):
        """Parameters for request_correction tool."""

        feedback: str = Field(
            description="What needs to be corrected and how to fix it"
        )

    async def execute(self, params: Params) -> None:
        """Verification signal - no action needed."""
        pass
