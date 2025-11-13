"""TaskExecutor - orchestrates Worker/Verifier loop for a single task."""

from datetime import datetime
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker import Worker
    from .verifier.verifier import Verifier

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
        sessions = []
        correction_count = 0
        result = None
        feedback = None

        while True:
            # Worker executes task
            worker_session = await self._worker.run(
                task_description=task_description,
                max_steps=20,
                resources=resources,
            )
            sessions.append(worker_session)

            # Verifier checks task
            verifier_session = await self._verifier.run(
                task_description=task_description,
                worker_session=worker_session,
                max_steps=5,
            )
            sessions.append(verifier_session)

            # Handle verifier decision
            if verifier_session.decision == VerifierDecision.COMPLETE_TASK:
                result = TaskResult.COMPLETE
                feedback = verifier_session.feedback
                break
            elif verifier_session.decision == VerifierDecision.REQUEST_CORRECTION:
                correction_count += 1
                if correction_count >= max_correction_attempts:
                    # Too many corrections - abort task
                    result = TaskResult.ABORTED
                    feedback = f"Exceeded {max_correction_attempts} correction attempts. Last feedback: {verifier_session.feedback}"
                    break
                # Continue loop for another Worker attempt
            elif verifier_session.decision == VerifierDecision.ABORT_TASK:
                result = TaskResult.ABORTED
                feedback = verifier_session.feedback
                break

        # Create and return TaskExecution with all collected data
        return TaskExecution(
            task_description=task_description,
            sessions=sessions,
            result=result,
            feedback=feedback,
            created_at=start_time,
            completed_at=datetime.now(),
        )
