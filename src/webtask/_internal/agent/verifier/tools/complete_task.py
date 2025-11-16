"""Verifier tool - complete task."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool
from ..verifier_session import VerifierDecision

if TYPE_CHECKING:
    from ..verifier import VerifierResult


class CompleteTaskTool(Tool):
    """Signal that task was successfully completed."""

    name = "complete_task"
    description = (
        "Signal that the task was successfully completed and all requirements were met"
    )
    is_terminal = True

    class Params(BaseModel):
        """Parameters for complete_task tool."""

        feedback: str = Field(
            description="What was accomplished and how requirements were met"
        )

    def __init__(self, verifier_result: "VerifierResult"):
        """Initialize with reference to verifier_result wrapper."""
        self.verifier_result = verifier_result

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of complete_task action."""
        return "Task completed"

    async def execute(self, params: Params) -> None:
        """Set verifier decision to complete."""
        self.verifier_result.decision = VerifierDecision.COMPLETE_TASK
        self.verifier_result.feedback = params.feedback
