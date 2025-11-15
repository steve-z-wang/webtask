"""TaskExecutor - orchestrates Worker/Verifier loop for a single task."""

from datetime import datetime
from typing import Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker import Worker
    from .verifier.verifier import Verifier
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession

from .task_execution import TaskExecution, TaskResult
from .verifier.verifier_session import VerifierDecision


class TaskExecutor:
    """Executes tasks with Worker/Verifier loop and correction retry logic."""

    def __init__(self, worker: "Worker", verifier: "Verifier"):
        self._worker = worker
        self._verifier = verifier

    async def run(
        self,
        task_description: str,
        max_correction_attempts: int = 3,
        resources: Optional[Dict[str, str]] = None,
    ) -> TaskExecution:
        """Execute task with Worker/Verifier loop and correction retry logic."""

        start_time = datetime.now()
        correction_count = 0
        sessions: List[Union["WorkerSession", "VerifierSession"]] = []
        worker_session, verifier_session = None, None
        verifier_result = None
        verifier_feedback = None

        while True:

            # Worker attempt (first time or correction retry)
            worker_session = await self._worker.run(
                task_description=task_description,
                max_steps=20,
                resources=(
                    resources if not sessions else None
                ),  # Resources only on first run
                previous_session=worker_session,
                verifier_feedback=(
                    verifier_session.feedback if verifier_session else None
                ),
            )
            sessions.append(worker_session)

            # Verifier checks result
            verifier_session = await self._verifier.run(
                task_description=task_description,
                max_steps=5,
                worker_summary=worker_session.action_summary,
                final_dom=worker_session.final_dom,
                final_screenshot=worker_session.final_screenshot,
                previous_session=verifier_session,
            )
            sessions.append(verifier_session)

            # Handle verifier decision
            if verifier_session.decision == VerifierDecision.COMPLETE_TASK:
                verifier_result = TaskResult.COMPLETE
                verifier_feedback = verifier_session.feedback
                break

            elif verifier_session.decision == VerifierDecision.ABORT_TASK:
                verifier_result = TaskResult.ABORTED
                verifier_feedback = verifier_session.feedback
                break

            elif verifier_session.decision == VerifierDecision.REQUEST_CORRECTION:
                if correction_count >= max_correction_attempts:
                    verifier_result = TaskResult.ABORTED
                    verifier_feedback = f"Exceeded {max_correction_attempts} correction attempts. Last feedback: {verifier_session.feedback}"
                    break

                # Prepare for correction retry
                correction_count += 1
                continue  # Loop back to worker

        # Create and return TaskExecution with all collected data
        return TaskExecution(
            task_description=task_description,
            sessions=sessions,
            result=verifier_result,
            feedback=verifier_feedback,
            created_at=start_time,
            completed_at=datetime.now(),
        )
