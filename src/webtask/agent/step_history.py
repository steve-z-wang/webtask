"""Step history - maintains record of agent cycles."""

from typing import List
from .step import Step
from ..llm import Block


class StepHistory:
    """
    Maintains history of completed agent steps.

    Each step represents a full cycle: proposal → execution → verification.
    """

    def __init__(self):
        """Initialize empty step history."""
        self._steps: List[Step] = []

    def add_step(self, step: Step) -> None:
        """
        Add a completed step to the history.

        Args:
            step: Step that was completed (proposal + execution + verification)
        """
        self._steps.append(step)

    def get_all(self) -> List[Step]:
        """
        Get all steps in history.

        Returns:
            List of all completed steps
        """
        return list(self._steps)

    def clear(self) -> None:
        """Clear all steps from history."""
        self._steps.clear()

    def to_context_block(self) -> Block:
        """
        Convert step history to context block for LLM.

        Returns:
            Block containing formatted step history
        """
        if not self._steps:
            return Block("Step History:\nNo steps executed yet.")

        lines = ["Step History:"]
        for i, step in enumerate(self._steps, 1):
            lines.append("")  # Single blank line before each step
            lines.append(f"Step {i}:")

            # Display all actions in this step
            for j, (action, execution) in enumerate(
                zip(step.proposals, step.executions), 1
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

            lines.append(
                f"  Verification: {'Complete' if step.verification.complete else 'Incomplete'}"
            )
            lines.append(f"  Message: {step.verification.message}")

        return Block("\n".join(lines))
