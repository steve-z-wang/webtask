"""TaskExecutor orchestrates manager, worker, and verifier to complete a task."""

from .task import TaskExecution
from .manager.manager import Manager
from .worker.worker import Worker
from .verifier.verifier import Verifier


class TaskExecutor:

    def __init__(self, manager: Manager, worker: Worker, verifier: Verifier):
        self._manager = manager
        self._worker = worker
        self._verifier = verifier

    async def run(self, task: TaskExecution, max_cycles: int = 10) -> TaskExecution:
        session_counter = 1
        last_verifier_session = None

        for cycle in range(max_cycles):
            # Manager plans subtasks
            manager_session = await self._manager.run(
                task_description=task.task.description,
                subtask_queue=task.subtask_queue,
                max_iterations=3,
                session_id=session_counter,
                last_verifier_session=last_verifier_session,
            )
            task.add_session(manager_session)
            session_counter += 1

            # Check if manager marked task as complete
            task_complete = any(
                tc.tool == "mark_task_complete" and tc.success
                for iteration in manager_session.iterations
                for tc in iteration.tool_calls
            )
            if task_complete:
                task.mark_complete()
                return task

            # Process pending subtasks until queue is empty or reschedule requested
            while task.subtask_queue.has_pending():
                # Pop next pending subtask
                current_subtask = task.subtask_queue.pop_next_pending()
                if current_subtask is None:
                    break

                # Mark current subtask as in progress
                current_subtask.mark_in_progress()

                # Worker executes subtask
                worker_session = await self._worker.run(
                    subtask_description=current_subtask.description,
                    max_iterations=10,
                    session_id=session_counter,
                )
                task.add_session(worker_session)
                session_counter += 1

                # Verifier checks subtask
                verifier_session = await self._verifier.run(
                    task_description=task.task.description,
                    subtask_description=current_subtask.description,
                    worker_session=worker_session,
                    max_iterations=3,
                    session_id=session_counter,
                )
                task.add_session(verifier_session)
                session_counter += 1

                # Store for next manager iteration
                last_verifier_session = verifier_session

                # Handle verifier decision
                if verifier_session.subtask_decision:
                    if verifier_session.subtask_decision.tool == "complete_subtask":
                        feedback = verifier_session.subtask_decision.parameters.get(
                            "feedback", ""
                        )
                        task.subtask_queue.mark_current_complete(feedback)
                    elif (
                        verifier_session.subtask_decision.tool == "request_reschedule"
                    ):
                        feedback = verifier_session.subtask_decision.parameters.get(
                            "feedback", ""
                        )
                        task.subtask_queue.mark_current_requested_reschedule(feedback)
                        # Break to return to Manager for replanning
                        break
                else:
                    # Verifier didn't make a decision - mark as requested reschedule
                    task.subtask_queue.mark_current_requested_reschedule(
                        "Verifier could not determine subtask status"
                    )
                    break

        return task
