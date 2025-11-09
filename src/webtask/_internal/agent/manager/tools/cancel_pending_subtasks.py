"""Cancel pending subtasks tool for Manager."""

from typing import TYPE_CHECKING
from pydantic import BaseModel
from ...tool import Tool

if TYPE_CHECKING:
    pass


class CancelPendingSubtasksTool(Tool):
    """Cancel all pending subtasks and move them to history as CANCELLED."""

    name = "cancel_pending_subtasks"
    description = "Cancel all pending subtasks in the queue and mark them as cancelled"

    class Params(BaseModel):
        pass

    async def execute(self, params: Params, **kwargs) -> None:
        """Cancel all pending subtasks.

        Args:
            params: Validated parameters (empty)
            **kwargs: subtask_queue injected by ToolRegistry
        """
        subtask_queue = kwargs.get("subtask_queue")

        # Cancel all pending subtasks and move to history
        subtask_queue.cancel_pending_subtasks()
