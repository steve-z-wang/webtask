"""Subtask queue for managing current subtask and history."""

from typing import List, Optional
from .subtask import Subtask, SubtaskStatus
from webtask._internal.llm import Block


class SubtaskQueue:
    """Manages current subtask, pending queue, and history of completed subtasks."""

    def __init__(self):
        self.current_subtask: Optional[Subtask] = None
        self.pending_subtasks: List[Subtask] = []
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

    def mark_current_complete(self, feedback: str) -> None:
        """Mark current subtask as complete.

        Args:
            feedback: Feedback about what was accomplished
        """
        if self.current_subtask:
            self.current_subtask.mark_complete(feedback)

    def mark_current_requested_reschedule(self, feedback: str) -> None:
        """Mark current subtask as requesting reschedule.

        Args:
            feedback: Explanation of why reschedule is needed
        """
        if self.current_subtask:
            self.current_subtask.mark_requested_reschedule(feedback)

    def get_all_subtasks(self) -> List[Subtask]:
        """Get all subtasks (history + current + pending)."""
        all_subtasks = list(self.history)
        if self.current_subtask:
            all_subtasks.append(self.current_subtask)
        all_subtasks.extend(self.pending_subtasks)
        return all_subtasks

    def add_subtask(self, goal: str) -> Subtask:
        """Add a new subtask to the pending queue.

        Args:
            goal: Description of the subtask goal

        Returns:
            The newly created subtask
        """
        subtask = Subtask(description=goal, status=SubtaskStatus.ASSIGNED)
        self.pending_subtasks.append(subtask)
        return subtask

    def cancel_pending_subtasks(self) -> None:
        """Cancel all pending subtasks (removes them without adding to history).

        Since these subtasks were never attempted, they don't need to be in history.
        """
        self.pending_subtasks = []

    def pop_next_pending(self) -> Optional[Subtask]:
        """Get next pending subtask and make it current.

        Moves current subtask to history if it exists.

        Returns:
            The next pending subtask, or None if queue is empty
        """
        if not self.pending_subtasks:
            return None

        # Move current to history if it exists
        if self.current_subtask is not None:
            self.history.append(self.current_subtask)

        # Pop next pending and make it current
        self.current_subtask = self.pending_subtasks.pop(0)
        return self.current_subtask

    def has_pending(self) -> bool:
        """Check if there are pending subtasks in the queue."""
        return len(self.pending_subtasks) > 0

    def __len__(self) -> int:
        """Get total number of subtasks (history + current + pending)."""
        return (
            len(self.history)
            + (1 if self.current_subtask else 0)
            + len(self.pending_subtasks)
        )

    def __str__(self) -> str:
        if not self.current_subtask and not self.history and not self.pending_subtasks:
            return "No subtasks"

        lines = []
        # Show history
        for i, subtask in enumerate(self.history):
            lines.append(f"  {i}. {subtask}")

        # Show current
        if self.current_subtask:
            lines.append(f"→ {len(self.history)}. {self.current_subtask}")

        # Show pending (assigned subtasks)
        for i, subtask in enumerate(self.pending_subtasks):
            idx = len(self.history) + (1 if self.current_subtask else 0) + i
            lines.append(f"  {idx}. [ASSIGNED] {subtask.description}")

        return "\n".join(lines)

    def get_context(self) -> Block:
        """Get formatted context for LLM."""
        if not self.current_subtask and not self.history and not self.pending_subtasks:
            return Block(heading="Subtask Queue", content="No subtasks created yet.")

        content = ""

        # Show history
        for i, subtask in enumerate(self.history):
            content += (
                f"  {i}. [{subtask.status.value.upper()}] {subtask.description}\n"
            )
            if subtask.feedback:
                content += f"     Feedback: {subtask.feedback}\n"

        # Show current
        if self.current_subtask:
            i = len(self.history)
            status = self.current_subtask.status.value.upper()
            content += f"→ {i}. [{status}] {self.current_subtask.description}\n"

        # Show pending (assigned subtasks)
        for i, subtask in enumerate(self.pending_subtasks):
            idx = len(self.history) + (1 if self.current_subtask else 0) + i
            content += f"  {idx}. [ASSIGNED] {subtask.description}\n"

        return Block(heading="Subtask Queue", content=content.strip())
