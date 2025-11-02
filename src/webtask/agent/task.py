"""Task context - all state for a single task execution."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .step import Step
from ..llm import Block


@dataclass
class Task:
    """
    Container for all task-scoped state.

    Created when a task is set, replaced when a new task starts.
    Owns task description, resources, and execution history.
    """

    description: str
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

            # Show proposed actions and their execution results
            if step.proposal.actions:
                summary_lines.append("  Actions taken:")
                for j, action in enumerate(step.proposal.actions):
                    # Show action with parameters
                    params_str = ", ".join(
                        f"{k}={v}" for k, v in action.parameters.model_dump().items()
                    )
                    action_line = (
                        f"    {j+1}. {action.tool}({params_str}) - {action.reason}"
                    )
                    summary_lines.append(action_line)

                    # Show execution result
                    if j < len(step.executions):
                        exec_result = step.executions[j]
                        if exec_result.success:
                            summary_lines.append("       ✓ Success")
                        else:
                            summary_lines.append(
                                f"       ✗ Failed: {exec_result.error}"
                            )

            # Show overall step result
            if step.proposal.complete:
                summary_lines.append("  Status: ✓ Task marked complete")
                summary_lines.append(f"  Message: {step.proposal.message}")
            else:
                summary_lines.append("  Status: Continuing...")
                summary_lines.append(f"  Message: {step.proposal.message}")

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
        return Block(f"Task:\n{self.description}")

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
