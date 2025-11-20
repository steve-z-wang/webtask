"""Task execution result and status."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any


class Status(str, Enum):
    """Task execution status."""

    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class Result:
    """Task execution result - lightweight result."""

    status: Optional[Status] = None
    output: Optional[Any] = None
    feedback: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        return self.status == Status.COMPLETED if self.status else False

    def __str__(self) -> str:
        status_str = self.status.value if self.status else "pending"
        return f"Result(status={status_str}, output={self.output is not None})"
