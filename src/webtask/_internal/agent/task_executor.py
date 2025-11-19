"""TaskExecutor - orchestrates Worker/Verifier loop for a single task."""

from datetime import datetime
from typing import Dict, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession
    from webtask.llm import LLM
    from .session_browser import SessionBrowser

from .task_execution import TaskExecution, TaskStatus, TaskResult
from .verifier.verifier_session import VerifierDecision
from .worker.worker import Worker
from .verifier.verifier import Verifier


class TaskExecutor:
    """Executes tasks with Worker/Verifier loop and correction retry logic."""

    def __init__(
        self,
        llm: "LLM",
        session_browser: "SessionBrowser",
        wait_after_action: float,
        resources: Optional[Dict[str, str]] = None,
        mode: str = "accessibility",
    ):
        self._worker = Worker(
            llm=llm,
            session_browser=session_browser,
            wait_after_action=wait_after_action,
            resources=resources,
            mode=mode,
        )
        self._verifier = Verifier(llm=llm, session_browser=session_browser)

    def _build_previous_history(
        self, sessions: List[Union["WorkerSession", "VerifierSession"]]
    ) -> Optional[str]:
        """Build previous history summary from all sessions except the last."""
        if len(sessions) <= 1:
            return None

        lines = []
        for session in sessions[:-1]:  # Exclude last session
            # Import here to avoid circular dependency
            from .worker.worker_session import WorkerSession
            from .verifier.verifier_session import VerifierSession

            if isinstance(session, WorkerSession):
                lines.append("Worker attempt:")
                lines.append(session.summary)
            elif isinstance(session, VerifierSession):
                lines.append(f"Verifier decision: {session.decision.value}")
                if session.feedback:
                    lines.append(f"Feedback: {session.feedback}")
                lines.append(f"Actions: {session.summary}")
            lines.append("")  # Blank line between sessions

        return "\n".join(lines)

    async def run(
        self,
        task_description: str,
        max_correction_attempts: int = 3,
    ) -> TaskResult:
        """Execute task with Worker/Verifier loop and correction retry logic."""

        start_time = datetime.now()
        correction_count = 0
        sessions: List[Union["WorkerSession", "VerifierSession"]] = []
        worker_session, verifier_session = None, None
        verifier_status = None
        verifier_feedback = None
        worker_output = None  # Track output from worker

        while True:

            worker_session = await self._worker.run(
                task_description=task_description,
                max_steps=20,
                previous_history=self._build_previous_history(sessions),
                verifier_feedback=(
                    verifier_session.feedback if verifier_session else None
                ),
            )
            sessions.append(worker_session)

            # Capture output from this worker session (last one wins)
            if worker_session.output is not None:
                worker_output = worker_session.output

            # Verifier checks result
            verifier_session = await self._verifier.run(
                task_description=task_description,
                max_steps=5,
                worker_actions=worker_session.summary,
                final_dom=worker_session.final_dom,
                final_screenshot=worker_session.final_screenshot,
                previous_history=self._build_previous_history(sessions),
            )
            sessions.append(verifier_session)

            # Handle verifier decision
            if verifier_session.decision == VerifierDecision.COMPLETE_TASK:
                verifier_status = TaskStatus.COMPLETE
                verifier_feedback = verifier_session.feedback
                break

            elif verifier_session.decision == VerifierDecision.ABORT_TASK:
                verifier_status = TaskStatus.ABORTED
                verifier_feedback = verifier_session.feedback
                break

            elif verifier_session.decision == VerifierDecision.REQUEST_CORRECTION:
                if correction_count >= max_correction_attempts:
                    verifier_status = TaskStatus.ABORTED
                    verifier_feedback = f"Exceeded {max_correction_attempts} correction attempts. Last feedback: {verifier_session.feedback}"
                    break

                # Prepare for correction retry
                correction_count += 1
                continue  # Loop back to worker

        # Create TaskExecution (internal execution history)
        task_execution = TaskExecution(
            task_description=task_description,
            sessions=sessions,
            status=verifier_status,
            created_at=start_time,
            completed_at=datetime.now(),
        )

        # Build and return user-facing TaskResult
        return TaskResult(
            status=verifier_status,
            output=worker_output,
            feedback=verifier_feedback,
            execution=task_execution,
        )
