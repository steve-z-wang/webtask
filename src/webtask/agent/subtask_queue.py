"""Subtask queue for managing current subtask and history."""

from typing import List, Optional
from .subtask import Subtask, SubtaskStatus
from ..llm import Block


class SubtaskQueue:
    """Manages current subtask and history of completed subtasks."""

    def __init__(self):
        self.current_subtask: Optional[Subtask] = None
        self.history: List[Subtask] = []

    def start_new(self, goal: str) -> Subtask:
        """Start a new subtask.

        If there's a current subtask, it gets moved to history first.

        Args:
            goal: Description of the subtask goal

        Returns:
            The newly created subtask
        """
        # Move current to history if it exists
        if self.current_subtask is not None:
            self.history.append(self.current_subtask)

        # Create and set new current subtask
        self.current_subtask = Subtask(description=goal, status=SubtaskStatus.PENDING)
        return self.current_subtask

    def get_current(self) -> Optional[Subtask]:
        """Get current subtask being worked on."""
        return self.current_subtask

    def mark_current_complete(self) -> None:
        """Mark current subtask as complete and move to history."""
        if self.current_subtask:
            self.current_subtask.mark_complete()

    def mark_current_failed(self, reason: str) -> None:
        """Mark current subtask as failed and move to history."""
        if self.current_subtask:
            self.current_subtask.mark_failed(reason)

    def get_all_subtasks(self) -> List[Subtask]:
        """Get all subtasks (history + current)."""
        all_subtasks = list(self.history)
        if self.current_subtask:
            all_subtasks.append(self.current_subtask)
        return all_subtasks

    def __len__(self) -> int:
        """Get total number of subtasks (history + current)."""
        return len(self.history) + (1 if self.current_subtask else 0)

    def __str__(self) -> str:
        if not self.current_subtask and not self.history:
            return "No subtasks"

        lines = []
        for i, subtask in enumerate(self.history):
            lines.append(f"  {i}. {subtask}")

        if self.current_subtask:
            lines.append(f"→ {len(self.history)}. {self.current_subtask}")

        return "\n".join(lines)

    def get_context(self) -> Block:
        """Get formatted context for LLM."""
        if not self.current_subtask and not self.history:
            return Block(heading="Subtask Queue", content="No subtasks created yet.")

        content = ""

        # Show history
        for i, subtask in enumerate(self.history):
            content += (
                f"  {i}. [{subtask.status.value.upper()}] {subtask.description}\n"
            )
            if subtask.failure_reason:
                content += f"     Failure: {subtask.failure_reason}\n"

        # Show current
        if self.current_subtask:
            i = len(self.history)
            status = self.current_subtask.status.value.upper()
            content += f"→ {i}. [{status}] {self.current_subtask.description}\n"

        return Block(heading="Subtask Queue", content=content.strip())
