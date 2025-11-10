"""SubtaskManager - orchestrates Worker/Verifier loop for a single subtask."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker import Worker
    from .verifier.verifier import Verifier

from .subtask import Subtask
from .subtask_execution import SubtaskExecution


class SubtaskManager:
    """Manages Worker/Verifier loop for subtask execution with correction retries."""

    def __init__(self, worker: "Worker", verifier: "Verifier"):
        self._worker = worker
        self._verifier = verifier

    async def run(
        self,
        subtask: Subtask,
        task_description: str,
        subtask_index: int,
        max_correction_attempts: int = 3,
    ) -> SubtaskExecution:
        """Execute subtask with Worker/Verifier loop and correction retry logic."""
        execution = SubtaskExecution(subtask=subtask)
        session_number = 1  # Reset to 1 for each subtask
        correction_count = 0

        while True:
            # Worker executes subtask
            worker_session = await self._worker.run(
                subtask_description=subtask.description,
                max_iterations=10,
                session_number=session_number,
                subtask_index=subtask_index,
                subtask_execution=execution,
            )
            execution.add_session(worker_session)
            session_number += 1

            # Verifier checks subtask
            verifier_session = await self._verifier.run(
                task_description=task_description,
                subtask_description=subtask.description,
                max_iterations=3,
                session_number=session_number,
                subtask_index=subtask_index,
                subtask_execution=execution,
            )
            execution.add_session(verifier_session)
            session_number += 1

            # Handle verifier decision
            if verifier_session.subtask_decision:
                if verifier_session.subtask_decision.tool == "complete_subtask":
                    feedback = verifier_session.subtask_decision.parameters.get(
                        "feedback", ""
                    )
                    subtask.mark_complete(feedback)
                    break
                elif verifier_session.subtask_decision.tool == "request_correction":
                    correction_count += 1
                    if correction_count >= max_correction_attempts:
                        # Too many corrections - force reschedule
                        subtask.mark_requested_reschedule(
                            f"Exceeded {max_correction_attempts} correction attempts"
                        )
                        break
                    # Continue loop for another Worker attempt
                elif verifier_session.subtask_decision.tool == "request_reschedule":
                    feedback = verifier_session.subtask_decision.parameters.get(
                        "feedback", ""
                    )
                    subtask.mark_requested_reschedule(feedback)
                    break
            else:
                # Verifier didn't make a decision
                subtask.mark_requested_reschedule(
                    "Verifier could not determine subtask status"
                )
                break

        return execution
