
from typing import List, Optional
from .subtask import Subtask, SubtaskStatus
from webtask._internal.llm import Block


class SubtaskQueue:

    def __init__(self):
        self.current_subtask: Optional[Subtask] = None
        self.pending_subtasks: List[Subtask] = []
        self.history: List[Subtask] = []

    def start_new(self, goal: str) -> Subtask:
        # Move current to history if it exists
        if self.current_subtask is not None:
            self.history.append(self.current_subtask)

        # Create and set new current subtask
        self.current_subtask = Subtask(description=goal, status=SubtaskStatus.PENDING)
        return self.current_subtask

    def get_current(self) -> Optional[Subtask]:
        return self.current_subtask

    def mark_current_complete(self, feedback: str) -> None:
        if self.current_subtask:
            self.current_subtask.mark_complete(feedback)

    def mark_current_requested_reschedule(self, feedback: str) -> None:
        if self.current_subtask:
            self.current_subtask.mark_requested_reschedule(feedback)

    def get_all_subtasks(self) -> List[Subtask]:
        all_subtasks = list(self.history)
        if self.current_subtask:
            all_subtasks.append(self.current_subtask)
        all_subtasks.extend(self.pending_subtasks)
        return all_subtasks

    def add_subtask(self, goal: str) -> Subtask:
        subtask = Subtask(description=goal, status=SubtaskStatus.ASSIGNED)
        self.pending_subtasks.append(subtask)
        return subtask

    def cancel_pending_subtasks(self) -> None:
        self.pending_subtasks = []

    def pop_next_pending(self) -> Optional[Subtask]:
        if not self.pending_subtasks:
            return None

        # Move current to history if it exists
        if self.current_subtask is not None:
            self.history.append(self.current_subtask)

        # Pop next pending and make it current
        self.current_subtask = self.pending_subtasks.pop(0)
        return self.current_subtask

    def has_pending(self) -> bool:
        return len(self.pending_subtasks) > 0

    def __len__(self) -> int:
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
