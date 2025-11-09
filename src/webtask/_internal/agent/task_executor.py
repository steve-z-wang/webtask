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

            current_subtask = task.subtask_queue.get_current()
            if current_subtask is None:
                break

            # Skip if subtask already completed or failed
            from .subtask import SubtaskStatus

            if current_subtask.status in [SubtaskStatus.COMPLETE, SubtaskStatus.FAILED]:
                break

            # Mark current subtask as in progress
            current_subtask.mark_in_progress()
            worker_session = await self._worker.run(
                subtask_description=current_subtask.description,
                max_iterations=10,
                session_id=session_counter,
            )
            task.add_session(worker_session)
            session_counter += 1

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

            if verifier_session.subtask_decision:
                if verifier_session.subtask_decision.tool == "mark_subtask_complete":
                    task.subtask_queue.mark_current_complete()
                elif verifier_session.subtask_decision.tool == "mark_subtask_failed":
                    task.subtask_queue.mark_current_failed(
                        verifier_session.subtask_decision.result
                    )
            else:
                task.subtask_queue.mark_current_failed(
                    "Verifier could not determine subtask status"
                )

        return task
