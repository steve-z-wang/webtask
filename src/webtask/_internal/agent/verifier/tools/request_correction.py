"""Verifier tool - request correction."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool
from ..verifier_session import VerifierDecision

if TYPE_CHECKING:
    from ..verifier import VerifierResult


class RequestCorrectionTool(Tool):
    """Request Worker to retry with feedback."""

    name = "request_correction"
    description = "Request Worker to retry the task with feedback to fix issues (use for small, fixable mistakes like wrong element clicked or typo)"
    is_terminal = True

    class Params(BaseModel):
        """Parameters for request_correction tool."""

        feedback: str = Field(
            description="What needs to be corrected and how to fix it"
        )

    def __init__(self, verifier_result: "VerifierResult"):
        """Initialize with reference to verifier_result wrapper."""
        self.verifier_result = verifier_result

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of request_correction action."""
        return "Requested correction"

    async def execute(self, params: Params) -> None:
        """Set verifier decision to request correction."""
        self.verifier_result.decision = VerifierDecision.REQUEST_CORRECTION
        self.verifier_result.feedback = params.feedback
