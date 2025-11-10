"""Start subtask execution tool for Manager."""

from typing import TYPE_CHECKING
from pydantic import BaseModel
from ...tool import Tool

if TYPE_CHECKING:
    pass


class StartSubtaskTool(Tool):
    """Signal to start executing the pending subtasks."""

    name = "start_subtask"
    description = "Signal that the pending subtask queue is ready for execution"

    class Params(BaseModel):
        pass

    async def execute(self, params: Params, **kwargs) -> None:
        """Signal to start execution.

        Args:
            params: Validated parameters (empty)
            **kwargs: Unused
        """
        pass
