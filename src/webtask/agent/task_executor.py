"""TaskExecutor orchestrates scheduler and worker to complete a task."""

from typing import Optional
from .task import TaskExecution
from .scheduler.scheduler import Scheduler
from .worker.worker import Worker
from .response import SchedulerSession, WorkerSession
from .subtask import SubtaskStatus
from .execution_logger import ExecutionLogger
from ..llm import LLM
from ..llm_browser import LLMBrowser


class TaskExecutor:
    """
    Orchestrates scheduler and worker to execute a task.

    Flow:
    1. Scheduler plans subtasks
    2. For each subtask:
       - Worker executes
       - If mark_subtask_complete → next subtask
       - If mark_subtask_failed → back to scheduler
    3. Task complete when all subtasks complete
    """

    def __init__(
        self,
        scheduler: Scheduler,
        worker: Worker,
        logger: Optional[ExecutionLogger] = None,
    ):
        """Initialize TaskExecutor.

        Args:
            scheduler: Scheduler instance (stateless)
            worker: Worker instance (stateless)
            logger: Optional ExecutionLogger for tracking execution events
        """
        self._scheduler = scheduler
        self._worker = worker
        self._logger = logger or ExecutionLogger()

    async def run(self, task: TaskExecution, max_cycles: int = 10) -> TaskExecution:
        """Execute task until complete or max cycles reached.

        Args:
            task: TaskExecution to execute
            max_cycles: Maximum scheduler→worker cycles

        Returns:
            TaskExecution with execution history
        """
        self._logger.log_task_start(task)

        # Initial planning
        self._logger.log_scheduler_session_start(task)
        scheduler_session = SchedulerSession(task=task, max_iterations=10)
        scheduler_session = await self._scheduler.run(scheduler_session)
        task.add_session(scheduler_session)
        self._logger.log_scheduler_session_complete(
            len(scheduler_session.iterations),
            len(task.subtask_queue.subtasks)
        )

        # Start with first subtask
        current_subtask = task.subtask_queue.get_current()
        if current_subtask is None:
            self._logger.log_task_complete(task)
            return task

        for cycle in range(max_cycles):
            current_index = task.subtask_queue.current_index

            # Worker executes subtask
            self._logger.log_worker_session_start(current_subtask, current_index)
            worker_session = WorkerSession(subtask=current_subtask, max_iterations=10)
            worker_session = await self._worker.run(worker_session)
            task.add_session(worker_session)
            self._logger.log_worker_session_complete(current_subtask, len(worker_session.iterations))

            # Check subtask status (worker already updated it)
            if current_subtask.status == SubtaskStatus.COMPLETE:
                # Move to next subtask
                next_subtask = task.subtask_queue.advance()
                if next_subtask is None:
                    # No more subtasks - task complete!
                    break
                self._logger.log_subtask_advance(current_index, task.subtask_queue.current_index)
                current_subtask = next_subtask

            elif current_subtask.status == SubtaskStatus.FAILED:
                # Run scheduler to replan
                self._logger.log_subtask_failed_replan(current_index)
                self._logger.log_scheduler_session_start(task)
                scheduler_session = SchedulerSession(task=task, max_iterations=10)
                scheduler_session = await self._scheduler.run(scheduler_session)
                task.add_session(scheduler_session)
                self._logger.log_scheduler_session_complete(
                    len(scheduler_session.iterations),
                    len(task.subtask_queue.subtasks)
                )
                # Get current subtask after replanning
                current_subtask = task.subtask_queue.get_current()
                if current_subtask is None:
                    # No subtasks after replanning
                    break

        self._logger.log_task_complete(task)
        return task
