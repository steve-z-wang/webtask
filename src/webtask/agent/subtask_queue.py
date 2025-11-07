"""Subtask queue for managing task execution order."""

from typing import List, Optional
from .subtask import Subtask, SubtaskStatus


class SubtaskQueue:
    """Manages queue of subtasks with status tracking."""

    def __init__(self):
        self._subtasks: List[Subtask] = []
        self._current_index: int = 0

    @property
    def subtasks(self) -> List[Subtask]:
        """Get all subtasks."""
        return self._subtasks

    @property
    def current_index(self) -> int:
        """Get current subtask index."""
        return self._current_index

    def add(self, description: str) -> None:
        """Add a new pending subtask to the end of queue."""
        subtask = Subtask(description=description, status=SubtaskStatus.PENDING)
        self._subtasks.append(subtask)

    def cancel(self, index: int) -> None:
        """Cancel a subtask at specific index."""
        if 0 <= index < len(self._subtasks):
            self._subtasks[index].mark_canceled()
        else:
            raise ValueError(
                f"Index {index} out of range (queue size: {len(self._subtasks)})"
            )

    def get_current(self) -> Optional[Subtask]:
        """Get current subtask being worked on."""
        if 0 <= self._current_index < len(self._subtasks):
            return self._subtasks[self._current_index]
        return None

    def advance(self) -> Optional[Subtask]:
        """Move to next subtask and return it (or None if at end)."""
        if self._current_index < len(self._subtasks) - 1:
            self._current_index += 1
            return self._subtasks[self._current_index]
        return None

    def __len__(self) -> int:
        """Get number of subtasks in queue."""
        return len(self._subtasks)

    def __str__(self) -> str:
        if not self._subtasks:
            return "No subtasks"

        lines = []
        for i, subtask in enumerate(self._subtasks):
            marker = "→" if i == self._current_index else " "
            lines.append(f"{marker} {i}. {subtask}")
        return "\n".join(lines)
