"""WorkerSession - tracks one worker.run() execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional
from webtask.llm import Message, AssistantMessage, ToolResultMessage


@dataclass
class WorkerSession:
    """Worker session with conversation history."""

    session_number: int
    subtask_description: str
    max_steps: int = 10
    steps_used: int = 0  # Number of steps actually used
    end_reason: Optional[Literal["complete_work", "abort_work", "max_steps"]] = None
    messages: List[Message] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        lines = ["=== Worker Session ==="]
        lines.append(f"Subtask: {self.subtask_description}")
        lines.append(f"Messages: {len(self.messages)}")
        lines.append("")

        # Show message summary
        for i, msg in enumerate(self.messages):
            msg_type = msg.__class__.__name__
            lines.append(f"[{i+1}] {msg_type}")

            if isinstance(msg, AssistantMessage):
                if msg.tool_calls:
                    lines.append(f"    Tool calls: {len(msg.tool_calls)}")
                    for tc in msg.tool_calls:
                        # Show tool name and description if available
                        if "description" in tc.arguments:
                            lines.append(f"      - {tc.name}: {tc.arguments['description']}")
                        else:
                            lines.append(f"      - {tc.name}")

            elif isinstance(msg, ToolResultMessage):
                lines.append(f"    Results: {len(msg.results)}")
                for result in msg.results:
                    status_str = f"{result.name}: {result.status}"
                    if result.error:
                        status_str += f" ({result.error})"
                    lines.append(f"      - {status_str}")

        return "\n".join(lines)
