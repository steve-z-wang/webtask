"""TaskExecutor orchestrates planner, worker, and verifier to complete a task."""

from typing import Optional
from .task import TaskExecution
from .planner.planner import Planner
from .worker.worker import Worker
from .verifier.verifier import Verifier
from .response import PlannerSession, WorkerSession, VerifierSession
from .subtask import SubtaskStatus
from .execution_logger import ExecutionLogger
from ..llm import LLM
from ..llm_browser import LLMBrowser


class TaskExecutor:
    """
    Orchestrates Planner→Worker→Verifier loop to execute a task.

    New adaptive architecture:
    Loop until task complete:
      1. Planner sees execution history and plans next subtask
      2. Worker executes subtask with browser actions
      3. Verifier checks if subtask succeeded and if task is complete
      4. If task complete: done
      5. If subtask failed: Planner will see failure and adjust
      6. If subtask succeeded: Planner will plan next step

    This is more robust than upfront planning - Planner adapts based on results.
    """

    def __init__(
        self,
        planner: Planner,
        worker: Worker,
        verifier: Verifier,
        logger: Optional[ExecutionLogger] = None,
    ):
        """Initialize TaskExecutor.

        Args:
            planner: Planner instance (stateless)
            worker: Worker instance (stateless)
            verifier: Verifier instance (stateless)
            logger: Optional ExecutionLogger for tracking execution events
        """
        self._planner = planner
        self._worker = worker
        self._verifier = verifier
        self._logger = logger or ExecutionLogger()

    async def run(self, task: TaskExecution, max_cycles: int = 10) -> TaskExecution:
        """Execute task with Planner→Worker→Verifier loop until complete.

        Args:
            task: TaskExecution to execute
            max_cycles: Maximum Planner→Worker→Verifier cycles

        Returns:
            TaskExecution with execution history and completion status
        """
        self._logger.log_task_start(task)

        for cycle in range(max_cycles):
            # 1. PLANNER: Plan next subtask based on execution history
            self._logger.log_planner_session_start(task)
            planner_session = PlannerSession(task=task, max_iterations=3)
            planner_session = await self._planner.run(planner_session)
            task.add_session(planner_session)
            self._logger.log_planner_session_complete(
                len(planner_session.iterations),
                len(task.subtask_queue.subtasks)
            )

            # Get current subtask (planner should have added one)
            current_subtask = task.subtask_queue.get_current()
            if current_subtask is None:
                # No subtasks planned - task may already be complete
                break

            current_index = task.subtask_queue.current_index

            # 2. WORKER: Execute the subtask
            self._logger.log_worker_session_start(current_subtask, current_index)
            worker_session = WorkerSession(subtask=current_subtask, max_iterations=10)
            worker_session = await self._worker.run(worker_session)
            task.add_session(worker_session)
            self._logger.log_worker_session_complete(current_subtask, len(worker_session.iterations))

            # 3. VERIFIER: Check if subtask succeeded and if task is complete
            self._logger.log_verifier_session_start(current_subtask, current_index)
            verifier_session = VerifierSession(
                subtask=current_subtask,
                worker_session=worker_session,
                task=task,
                max_iterations=3
            )
            verifier_session = await self._verifier.run(verifier_session)
            task.add_session(verifier_session)
            self._logger.log_verifier_session_complete(
                current_subtask,
                len(verifier_session.iterations),
                verifier_session.task_complete
            )

            # Check if task is complete
            if verifier_session.task_complete:
                self._logger.log_task_complete(task)
                return task

            # Check subtask status (verifier updated it)
            if current_subtask.status == SubtaskStatus.COMPLETE:
                # Move to next subtask
                next_subtask = task.subtask_queue.advance()
                if next_subtask is None:
                    # No more subtasks in queue, but task not marked complete
                    # Planner will decide what to do next
                    pass
                else:
                    self._logger.log_subtask_advance(current_index, task.subtask_queue.current_index)

            elif current_subtask.status == SubtaskStatus.FAILED:
                # Subtask failed - move past it, Planner will see failure and adjust
                self._logger.log_subtask_failed_replan(current_index)
                task.subtask_queue.advance()

        # Max cycles reached without completion
        self._logger.log_task_complete(task)
        return task
