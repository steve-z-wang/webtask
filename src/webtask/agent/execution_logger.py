"""ExecutionLogger for centralized execution event tracking."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .task import TaskExecution
    from .subtask import Subtask
    from .tool_call import ToolCall


class ExecutionLogger:
    """Centralized execution event logger that tracks execution flow."""

    def __init__(self, enabled: bool = False):
        """
        Initialize ExecutionLogger.

        Args:
            enabled: Whether to enable logging (default: False - disabled)
        """
        self.enabled = enabled
        self.logger = logging.getLogger("webtask.execution") if enabled else None

    # Task-level events (INFO)
    def log_task_start(self, task: "TaskExecution") -> None:
        """Log when task execution begins."""
        if not self.enabled:
            return
        self.logger.info(f"[Task] Starting: {task.description}")

    def log_task_complete(self, task: "TaskExecution") -> None:
        """Log when task execution completes."""
        if not self.enabled:
            return
        completed = sum(1 for s in task.subtask_queue.subtasks if s.status.value == "complete")
        total = len(task.subtask_queue.subtasks)
        self.logger.info(f"[Task] Complete: {completed}/{total} subtasks done")

    # Session-level events (INFO)
    def log_planner_session_start(self, task: "TaskExecution") -> None:
        """Log when planner session begins."""
        if not self.enabled:
            return
        self.logger.info("[Planner] Planning next subtask...")

    def log_planner_session_complete(self, num_iterations: int, num_subtasks: int) -> None:
        """Log when planner session completes."""
        if not self.enabled:
            return
        self.logger.info(f"[Planner] Planning complete: {num_iterations} iterations, {num_subtasks} total subtasks")

    def log_worker_session_start(self, subtask: "Subtask", subtask_index: int) -> None:
        """Log when worker session begins."""
        if not self.enabled:
            return
        self.logger.info(f"[Worker] Executing subtask {subtask_index}: {subtask.description}")

    def log_worker_session_complete(self, subtask: "Subtask", num_iterations: int) -> None:
        """Log when worker session completes."""
        if not self.enabled:
            return
        self.logger.info(f"[Worker] Execution complete: {num_iterations} iterations")

    def log_verifier_session_start(self, subtask: "Subtask", subtask_index: int) -> None:
        """Log when verifier session begins."""
        if not self.enabled:
            return
        self.logger.info(f"[Verifier] Verifying subtask {subtask_index}...")

    def log_verifier_session_complete(self, subtask: "Subtask", num_iterations: int, task_complete: bool) -> None:
        """Log when verifier session completes."""
        if not self.enabled:
            return
        status_msg = f"Subtask {subtask.status.value}"
        if task_complete:
            status_msg += ", Task COMPLETE"
        self.logger.info(f"[Verifier] {status_msg}: {num_iterations} iterations")

    # Iteration-level events (DEBUG)
    def log_iteration_start(self, role: str, iteration_num: int) -> None:
        """Log when an iteration starts."""
        if not self.enabled:
            return
        self.logger.debug(f"[{role}] Iteration {iteration_num}: Generating...")

    def log_iteration_complete(self, role: str, iteration_num: int, message: str, tool_count: int) -> None:
        """Log when an iteration completes."""
        if not self.enabled:
            return
        # Truncate message for readability
        message_preview = message[:80] + "..." if len(message) > 80 else message
        self.logger.debug(f"[{role}] Iteration {iteration_num}: {message_preview} ({tool_count} tools)")

    def log_tool_call(self, role: str, tool_call: "ToolCall") -> None:
        """Log a tool call execution."""
        if not self.enabled:
            return
        status = "✓" if tool_call.success else "✗"

        # Format parameters concisely
        params_str = self._format_params(tool_call.parameters)

        # Log worker actions at INFO level (so users see what's happening)
        # Log planner/verifier actions at DEBUG level (less important)
        if role == "Worker":
            self.logger.info(f"  → {tool_call.tool}({params_str})")
        else:
            self.logger.debug(f"[{role}] {status} {tool_call.tool}({params_str})")

    def _format_params(self, params: dict) -> str:
        """Format parameters concisely for logging."""
        if not params:
            return ""

        # Limit each parameter value to 60 chars
        formatted = []
        for key, value in params.items():
            value_str = str(value)
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."
            formatted.append(f"{key}={value_str}")

        return ", ".join(formatted)

    # Transition events (INFO)
    def log_subtask_advance(self, from_index: int, to_index: int) -> None:
        """Log when advancing to next subtask."""
        if not self.enabled:
            return
        self.logger.info(f"[TaskExecutor] Advancing from subtask {from_index} to {to_index}")

    def log_subtask_failed_replan(self, subtask_index: int) -> None:
        """Log when subtask fails and needs replanning."""
        if not self.enabled:
            return
        self.logger.info(f"[TaskExecutor] Subtask {subtask_index} failed, Planner will adapt")
