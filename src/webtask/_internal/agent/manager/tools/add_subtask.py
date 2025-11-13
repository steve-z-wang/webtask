
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    pass


class AddSubtaskTool(Tool):

    name = "add_subtask"
    description = "Add a new subtask to the pending queue with the given goal"

    class Params(BaseModel):
        goal: str = Field(description="Subtask goal to achieve")

    async def execute(self, params: Params, **kwargs) -> None:
        subtask_queue = kwargs.get("subtask_queue")

        # Add subtask to pending queue
        subtask_queue.add_subtask(params.goal)
