"""Verifier tool - abort task."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool
from ..verifier_session import VerifierDecision

if TYPE_CHECKING:
    from ..verifier import VerifierResult


class AbortTaskTool(Tool):
    """Signal that task cannot be completed."""

    name = "abort_task"
    description = "Signal that the task cannot be completed due to unfixable blocker (e.g., wrong approach, impossible requirement, bot challenge, permanent error)"
    is_terminal = True

    class Params(BaseModel):
        """Parameters for abort_task tool."""

        feedback: str = Field(
            description="Explanation of why task cannot be completed - what went wrong, what was tried, what blocked progress"
        )

    def __init__(self, verifier_result: "VerifierResult"):
        """Initialize with reference to verifier_result wrapper."""
        self.verifier_result = verifier_result

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of abort_task action."""
        return "Task aborted"

    async def execute(self, params: Params) -> None:
        """Set verifier decision to abort."""
        self.verifier_result.decision = VerifierDecision.ABORT_TASK
        self.verifier_result.feedback = params.feedback
