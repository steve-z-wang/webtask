"""Control tools for task flow management."""

from typing import Any, Optional, Type, TYPE_CHECKING
from pydantic import BaseModel, Field, create_model
from webtask.llm.tool import Tool, ToolParams
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.run import TaskResult


class CompleteWorkTool(Tool):
    """Signal that the worker has successfully completed the subtask with optional output data."""

    name = "complete_work"
    description = "Signal that you have successfully completed the subtask. Optionally provide structured output data to return to the user."

    # Default Params class (will be overridden in __init__ if output_schema is provided)
    class Params(ToolParams):
        """Parameters for complete_work tool."""

        feedback: str = Field(
            description="Brief 1-2 sentence summary of what you accomplished"
        )
        output: Optional[Any] = Field(
            default=None,
            description="Optional structured data to return to the user (e.g., extracted information, results)",
        )

    def __init__(
        self, task_result: "TaskResult", output_schema: Optional[Type[BaseModel]] = None
    ):
        """Initialize with reference to worker result and optional output schema.

        Args:
            task_result: TaskResult object to store completion status and data
            output_schema: Optional Pydantic model class defining the expected output structure
        """
        from webtask._internal.agent.run import TaskStatus

        self.task_result = task_result
        self._TaskStatus = TaskStatus

        # Dynamically create Params class if output_schema is provided
        if output_schema:
            # Inherit from base Params and only override the output field with the schema
            # This shadows the class-level Params attribute for this instance
            self.Params = create_model(  # type: ignore[misc]
                "CompleteWorkParams",
                __base__=CompleteWorkTool.Params,
                output=(
                    Optional[output_schema],
                    Field(
                        default=None,
                        description="Structured output data matching the specified schema",
                    ),
                ),
            )
        # Otherwise, the default class-level Params will be used

    async def execute(self, params: Params) -> ToolResult:
        """Signal that work is complete and store feedback and optional output."""
        self.task_result.status = self._TaskStatus.COMPLETED
        self.task_result.feedback = params.feedback
        if params.output is not None:
            self.task_result.output = params.output

        desc = f"Completed: {params.feedback}"
        if params.output is not None:
            try:
                import json

                output_str = json.dumps(params.output, indent=2, ensure_ascii=False)
                desc += f"\nOutput data:\n{output_str}"
            except (TypeError, ValueError):
                desc += f"\nOutput data: {params.output}"

        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=desc,
            terminal=True,
        )


class AbortWorkTool(Tool):
    """Signal that the worker cannot proceed further with the subtask."""

    name = "abort_work"
    description = "Signal that you cannot proceed further with this subtask (stuck, blocked, error, or impossible to complete)"

    class Params(ToolParams):
        """Parameters for abort_work tool."""

        reason: str = Field(
            description="Explain why you cannot continue and provide any relevant context about what went wrong or what is blocking you"
        )

    def __init__(self, task_result: "TaskResult"):
        """Initialize with reference to worker result."""
        from webtask._internal.agent.run import TaskStatus

        self.task_result = task_result
        self._TaskStatus = TaskStatus

    async def execute(self, params: Params) -> ToolResult:
        """Signal that work is aborted and store reason as feedback."""
        self.task_result.status = self._TaskStatus.ABORTED
        self.task_result.feedback = params.reason

        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Aborted: {params.reason}",
            terminal=True,
        )
