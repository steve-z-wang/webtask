"""Task execution - all classes for task state and task executor."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel
from .schemas.proposal import Proposal, RoleType
from .role import ActionResult
from ..llm import Block

if TYPE_CHECKING:
    from ..llm import LLM
    from ..llm_browser import LLMBrowser


class Step(BaseModel):
    """Represents one complete agent cycle (propose actions → execute actions)."""

    proposal: Proposal
    executions: List[ActionResult]

    @property
    def is_complete(self) -> bool:
        """Check if task is complete (mark_complete tool was called)."""
        return any(action.tool == "mark_complete" for action in self.proposal.actions)


class TaskResult(BaseModel):
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str


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

            # Show proposal and execution results
            actions = step.proposal.actions
            if actions:
                summary_lines.append("  Actions taken:")
                for j, action in enumerate(actions):
                    # Show action with parameters
                    params_str = ", ".join(
                        f"{k}={v}" for k, v in action.parameters.items()
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
            if step.is_complete:
                summary_lines.append("  Status: ✓ Task marked complete")
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


class TaskExecutor:
    """
    Executes a task with roles.

    Responsibilities:
    - Execute task (does NOT own task - Agent owns it)
    - Create and own throttler (per-task rate limiting)
    - Create and own roles (VerifierRole, ProposerRole)
    - Execute full cycle: select role → propose → execute → record step
    - Track current role and handle transitions
    - Run autonomous execution loop
    """

    def __init__(
        self,
        task: Task,
        llm: "LLM",
        llm_browser: "LLMBrowser",
        action_delay: float = 1.0,
    ):
        """
        Initialize task executor.

        Args:
            task: Task to execute (owned by Agent)
            llm: LLM instance for reasoning
            llm_browser: Browser interface for page context
            action_delay: Delay in seconds after actions (default: 1.0)
        """
        from .roles import VerifierRole, ProposerRole
        from ..utils.throttler import Throttler

        self.task = task

        # Create throttler (per-task rate limiting)
        throttler = Throttler(delay=action_delay)

        # Track current role
        self.current_role = RoleType.PROPOSE

        # Initialize all roles (validation logic is in BaseRole)
        self.verifier = VerifierRole(
            llm=llm,
            task_context=task,
            llm_browser=llm_browser,
            throttler=throttler,
        )

        self.proposer = ProposerRole(
            llm=llm,
            task_context=task,
            llm_browser=llm_browser,
            throttler=throttler,
        )

    async def run_step(self) -> Step:
        """
        Execute one complete step of the task.

        Flow:
        1. Select role based on current role
        2. Role proposes actions (thinking)
        3. Role executes actions (doing)
        4. Create step from proposal + execution results
        5. Record step in task history
        6. Transition to next role

        Returns:
            Step with proposal and execution results
        """
        # Select role based on current role
        if self.current_role == RoleType.VERIFY:
            current_role = self.verifier
        elif self.current_role == RoleType.PROPOSE:
            current_role = self.proposer
        else:
            raise ValueError(f"Unknown role: {self.current_role}")

        # Propose actions (thinking)
        proposal = await current_role.propose_actions()

        # Execute actions (doing)
        exec_results = []
        if proposal.actions:
            exec_results = await current_role.execute(proposal.actions)

        # Create step
        step = Step(proposal=proposal, executions=exec_results)

        # Record step in task history
        self.task.add_step(step)

        # Transition to next role
        self.current_role = proposal.next_role

        return step

    async def execute(self) -> TaskResult:
        """
        Execute the task autonomously.

        Runs steps until task is complete or max_steps reached.

        Returns:
            TaskResult with completion status, steps, and final message
        """
        for i in range(self.task.max_steps):
            step = await self.run_step()

            if step.is_complete:
                return TaskResult(
                    completed=True,
                    steps=self.task.steps,
                    message=step.proposal.message,
                )

        return TaskResult(
            completed=False,
            steps=self.task.steps,
            message=f"Task not completed after {self.task.max_steps} steps",
        )
