"""Task context - all state for a single task execution."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .step import Step
from ..llm import Block


@dataclass
class TaskContext:
    """
    Container for all task-scoped state.

    Created when a task is set, replaced when a new task starts.
    Owns task description, resources, and execution history.
    """

    task: str
    """Task description in natural language."""

    resources: Dict[str, str] = field(default_factory=dict)
    """File resources available to this task (name -> path)."""

    steps: List[Step] = field(default_factory=list)
    """Execution history for this task."""

    max_steps: int = 10
    """Maximum steps before giving up."""

    def add_step(self, step: Step) -> None:
        """
        Add a completed step to history.

        Args:
            step: Completed step with proposal and execution results
        """
        self.steps.append(step)

    def get_steps_summary(self) -> str:
        """
        Format step history for LLM context.

        Returns:
            Human-readable summary of completed steps
        """
        if not self.steps:
            return "No previous steps."

        summary_lines = []
        for i, step in enumerate(self.steps, 1):
            summary_lines.append(f"\nStep {i}:")

            # Show proposed actions
            if step.proposal.actions:
                summary_lines.append("  Actions:")
                for action in step.proposal.actions:
                    summary_lines.append(
                        f"    - {action.tool_name}: {action.reason}"
                    )

            # Show result
            if step.proposal.complete:
                summary_lines.append(
                    f"  Result: ✓ Task complete - {step.proposal.message}"
                )
            else:
                summary_lines.append(f"  Result: {step.proposal.message}")

        return "\n".join(summary_lines)

    @property
    def step_count(self) -> int:
        """Number of completed steps."""
        return len(self.steps)

    def get_task_context(self) -> Block:
        """
        Get formatted task context for LLM.

        Returns:
            Block containing the task description
        """
        return Block(f"Task:\n{self.task}")

    def get_resources_context(self) -> Optional[Block]:
        """
        Get formatted resources context for LLM.

        Returns:
            Block containing available resources, or None if no resources
        """
        if not self.resources:
            return None

        resources_text = "Available file resources for upload:\n"
        for name, path in self.resources.items():
            resources_text += f"- {name}: {path}\n"

        return Block(resources_text)

    def get_steps_context(self) -> Block:
        """
        Get formatted step history context for LLM.

        Returns:
            Block containing the formatted step history
        """
        return Block(f"Previous steps:\n{self.get_steps_summary()}")
