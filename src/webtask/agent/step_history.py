"""Step history - maintains record of agent cycles."""

from typing import List
from .step import Step
from ..llm import Block


class StepHistory:
    """Maintains history of completed agent steps."""

    def __init__(self):
        self._steps: List[Step] = []

    def add_step(self, step: Step) -> None:
        """Add a completed step to the history."""
        self._steps.append(step)

    def get_all(self) -> List[Step]:
        """Get all steps in history."""
        return list(self._steps)

    def clear(self) -> None:
        """Clear all steps from history."""
        self._steps.clear()

    def to_context_block(self) -> Block:
        """Convert step history to context block for LLM."""
        if not self._steps:
            return Block("Step History:\nNo steps executed yet.")

        lines = ["Step History:"]
        for i, step in enumerate(self._steps, 1):
            lines.append("")
            lines.append(f"Step {i}:")

            # Show completion status and message first
            lines.append(
                f"  Status: {'Complete' if step.proposal.complete else 'Incomplete'}"
            )
            lines.append(f"  Message: {step.proposal.message}")

            # Show actions and execution results
            for j, (action, execution) in enumerate(
                zip(step.proposal.actions, step.executions), 1
            ):
                lines.append(f"  Action {j}:")
                lines.append(f"    Tool: {action.tool_name}")
                lines.append(f"    Reason: {action.reason}")
                lines.append(f"    Parameters: {action.parameters}")
                lines.append(
                    f"    Execution: {'Success' if execution.success else 'Failed'}"
                )
                if execution.error:
                    lines.append(f"    Error: {execution.error}")

        return Block("\n".join(lines))
