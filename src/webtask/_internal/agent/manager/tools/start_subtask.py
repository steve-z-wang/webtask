
from typing import TYPE_CHECKING
from pydantic import BaseModel
from ...tool import Tool

if TYPE_CHECKING:
    pass


class StartSubtaskTool(Tool):

    name = "start_subtask"
    description = "Signal that the pending subtask queue is ready for execution"

    class Params(BaseModel):
        pass

    async def execute(self, params: Params, **kwargs) -> None:
        pass
