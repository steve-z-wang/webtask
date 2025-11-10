"""TaskExecutor orchestrates manager, worker, and verifier to complete a task."""

from .task import TaskExecution
from .manager.manager import Manager
from .worker.worker import Worker
from .verifier.verifier import Verifier
from .subtask_manager import SubtaskManager


class TaskExecutor:

    def __init__(self, manager: Manager, worker: Worker, verifier: Verifier):
        self._manager = manager
        self._subtask_manager = SubtaskManager(worker, verifier)

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

            # Check if manager marked task as completed or aborted
            task_completed = any(
                tc.tool == "complete_task" and tc.success
                for iteration in manager_session.iterations
                for tc in iteration.tool_calls
            )
            if task_completed:
                task.mark_completed()
                return task

            task_aborted = any(
                tc.tool == "abort_task" and tc.success
                for iteration in manager_session.iterations
                for tc in iteration.tool_calls
            )
            if task_aborted:
                # Extract abort reason from the tool call
                for iteration in manager_session.iterations:
                    for tc in iteration.tool_calls:
                        if tc.tool == "abort_task" and tc.success:
                            reason = tc.parameters.get("reason", "Unknown reason")
                            task.mark_aborted(reason)
                            return task

            # Process pending subtasks until queue is empty or reschedule requested
            while task.subtask_queue.has_pending():
                # Pop next pending subtask
                current_subtask = task.subtask_queue.pop_next_pending()
                if current_subtask is None:
                    break

                # Mark current subtask as in progress
                current_subtask.mark_in_progress()

                # Subtask index is the position in history (0-indexed)
                subtask_index = len(task.subtask_queue.history)

                # Execute subtask with SubtaskManager (handles Worker/Verifier loop with corrections)
                subtask_execution = await self._subtask_manager.run(
                    subtask=current_subtask,
                    task_description=task.task.description,
                    subtask_index=subtask_index,
                )
                task.add_session(subtask_execution)

                # Store last verifier session for next manager iteration
                if subtask_execution.history:
                    from .verifier.verifier_session import VerifierSession

                    last_session = subtask_execution.history[-1]
                    if isinstance(last_session, VerifierSession):
                        last_verifier_session = last_session

                # Break to return to Manager if reschedule requested
                from .subtask import SubtaskStatus

                if current_subtask.status == SubtaskStatus.REQUESTED_RESCHEDULE:
                    break

        return task
