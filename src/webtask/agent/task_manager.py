"""Task manager - manages task execution with roles."""

from typing import Dict, Optional
from .roles import VerifierRole, ProposerRole
from .schemas.mode import Mode
from .step import Step, TaskResult
from ..llm import LLM, ValidatedLLM
from .task import Task
from ..llm_browser import LLMBrowser
from ..utils.throttler import Throttler


class TaskManager:
    """
    Manages complete task execution.

    Responsibilities:
    - Create and own task state and history
    - Create and own throttler (per-task rate limiting)
    - Create and own roles (VerifierRole, ProposerRole)
    - Execute full cycle: select role → propose → execute → record step
    - Track current mode and handle transitions
    - Run autonomous execution loop
    """

    def __init__(
        self,
        task_description: str,
        llm: LLM,
        llm_browser: LLMBrowser,
        action_delay: float = 1.0,
        max_steps: int = 10,
        resources: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize task manager.

        Args:
            task_description: Task description in natural language
            llm: LLM instance for reasoning
            llm_browser: Browser interface for page context
            action_delay: Delay in seconds after actions (default: 1.0)
            max_steps: Maximum steps before giving up (default: 10)
            resources: Optional dict of file resources (name -> path)
        """
        # Create task
        self.task = Task(
            description=task_description,
            resources=resources or {},
            max_steps=max_steps,
        )

        # Create throttler (per-task rate limiting)
        throttler = Throttler(delay=action_delay)

        # Create validated LLM wrapper
        validated_llm = ValidatedLLM(llm)

        # Track current mode
        self.current_mode = Mode.PROPOSE

        # Initialize all roles
        self.verifier = VerifierRole(
            validated_llm=validated_llm,
            task_context=self.task,
            llm_browser=llm_browser,
            throttler=throttler,
        )

        self.proposer = ProposerRole(
            validated_llm=validated_llm,
            task_context=self.task,
            llm_browser=llm_browser,
            throttler=throttler,
        )

    async def run_step(self) -> Step:
        """
        Execute one complete step of the task.

        Flow:
        1. Select role based on current mode
        2. Role proposes actions (thinking)
        3. Role executes actions (doing)
        4. Create step from proposal + execution results
        5. Record step in task history
        6. Transition to next mode

        Returns:
            Step with proposal and execution results
        """
        # Select role based on current mode
        if self.current_mode == Mode.VERIFY:
            current_role = self.verifier
        elif self.current_mode == Mode.PROPOSE:
            current_role = self.proposer
        else:
            raise ValueError(f"Unknown mode: {self.current_mode}")

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

        # Transition to next mode
        self.current_mode = proposal.next_mode

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
