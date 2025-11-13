"""TaskExecution - execution history for one task."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession


class TaskResult(str, Enum):
    """Task execution result."""
    COMPLETE = "complete_task"
    ABORTED = "abort_task"


@dataclass
class TaskExecution:
    """Execution history for one task - pure data container."""

    task_description: str
    sessions: List[Union["WorkerSession", "VerifierSession"]]
    result: TaskResult
    feedback: str
    created_at: datetime
    completed_at: datetime
