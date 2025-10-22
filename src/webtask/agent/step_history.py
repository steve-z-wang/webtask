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
            return Block("No steps executed yet.")

        history = Block("Step History:")
        for i, step in enumerate(self._steps, 1):
            step_block = Block(f"Step {i}:")

            # Display all actions in this step
            for j, (action, execution) in enumerate(
                zip(step.proposals, step.executions), 1
            ):
                action_block = Block(f"  Action {j}:")
                action_block.append(f"  Tool: {action.tool_name}")
                action_block.append(f"  Reason: {action.reason}")
                action_block.append(f"  Parameters: {action.parameters}")
                action_block.append(
                    f"  Execution: {'Success' if execution.success else 'Failed'}"
                )
                if execution.error:
                    action_block.append(f"  Error: {execution.error}")
                step_block.append(action_block)

            step_block.append(
                f"Verification: {'Complete' if step.verification.complete else 'Incomplete'}"
            )
            step_block.append(f"Message: {step.verification.message}")
            history.append(step_block)

        return history
