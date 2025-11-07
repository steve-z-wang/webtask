"""Context builder for SubtaskQueue."""

from typing import TYPE_CHECKING
from ...llm import Block

if TYPE_CHECKING:
    from ..subtask_queue import SubtaskQueue


class SubtaskQueueContextBuilder:
    """Builds LLM context blocks from SubtaskQueue."""

    def __init__(self, subtask_queue: "SubtaskQueue"):
        self._subtask_queue = subtask_queue

    def build_queue_context(self) -> Block:
        """Format queue as LLM context block."""
        subtasks = self._subtask_queue.subtasks
        current_index = self._subtask_queue.current_index

        if not subtasks:
            return Block(heading="Subtask Queue", content="No subtasks created yet.")

        content = ""
        for i, subtask in enumerate(subtasks):
            # Mark current subtask
            marker = "→" if i == current_index else " "

            # Format: index, status, description
            content += f"{marker} {i}. [{subtask.status.value.upper()}] {subtask.description}\n"

            # Add failure reason if failed
            if subtask.failure_reason:
                content += f"   Failure: {subtask.failure_reason}\n"

        return Block(heading="Subtask Queue", content=content.strip())
