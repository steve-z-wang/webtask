"""Verifier tool - request correction."""

from pydantic import BaseModel, Field
from ...tool import Tool


class RequestCorrectionTool(Tool):
    """Request Worker to fix issues without replanning."""

    name = "request_correction"
    description = "Request Worker to make corrections to fix issues (use when fixable without replanning)"

    class Params(BaseModel):
        """Parameters for request_correction tool."""

        feedback: str = Field(
            description="What needs to be corrected and how to fix it"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Verification signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
