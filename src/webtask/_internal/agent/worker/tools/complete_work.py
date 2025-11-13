"""Worker tool - signal successful completion of subtask."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class CompleteWorkTool(Tool):
    """Signal that the worker has successfully completed the subtask."""

    name = "complete_work"
    description = "Signal that you have successfully completed the subtask"

    class Params(BaseModel):
        """Parameters for complete_work tool."""

        feedback: str = Field(
            description="Describe what you accomplished and provide any important context or knowledge that might be useful for future subtasks in this task"
        )

    async def execute(self, params: Params) -> None:
        """Signal that work is complete."""
        pass
