"""Mark Complete tool - signals task completion."""

from ...tool import Tool
from ...schemas import ToolParams
from pydantic import Field


class MarkCompleteParams(ToolParams):
    """Parameters for mark_complete tool."""

    reason: str = Field(description="Why the task is now complete")


class MarkCompleteTool(Tool[MarkCompleteParams]):
    """
    Special control flow tool that signals task completion.

    This tool doesn't perform any browser actions - it's a signal
    that the task is complete. Used by VERIFY role.
    """

    @property
    def name(self) -> str:
        return "mark_complete"

    @property
    def description(self) -> str:
        return "Mark the task as complete. Use this when all task requirements are satisfied and verified on the page."

    @property
    def params_class(self):
        return MarkCompleteParams

    async def execute(self, params: MarkCompleteParams):
        """
        Execute mark_complete (no-op, just signals completion).

        The presence of this tool in actions indicates task completion.
        """
        # No-op: completion is signaled by the tool's presence
        pass
