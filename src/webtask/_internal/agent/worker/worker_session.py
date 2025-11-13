
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from ....llm.message import Message, SystemMessage, UserMessage, AssistantMessage, ToolResultMessage


@dataclass
class WorkerSession:

    subtask_description: str
    status: str  # "completed", "failed", "max_iterations"
    message_history: List[Message]
    iterations_count: int
    final_url: str
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def __str__(self) -> str:
        lines = ["=== Worker Session ==="]
        lines.append(f"Subtask: {self.subtask_description}")
        lines.append(f"Status: {self.status}")
        lines.append(f"Iterations: {self.iterations_count}")
        lines.append(f"Final URL: {self.final_url}")
        if self.error:
            lines.append(f"Error: {self.error}")
        lines.append("")
        lines.append(f"Message History ({len(self.message_history)} messages):")

        for i, msg in enumerate(self.message_history):
            msg_type = msg.__class__.__name__
            lines.append(f"  [{i+1}] {msg_type}")

            if isinstance(msg, (SystemMessage, UserMessage)):
                # Show content summary
                if msg.content:
                    text_count = sum(1 for c in msg.content if hasattr(c, 'text'))
                    image_count = sum(1 for c in msg.content if hasattr(c, 'data'))
                    lines.append(f"      Content: {text_count} text, {image_count} images")

            elif isinstance(msg, AssistantMessage):
                if msg.content:
                    lines.append(f"      Text: {len(msg.content)} parts")
                if msg.tool_calls:
                    lines.append(f"      Tool Calls: {len(msg.tool_calls)}")
                    for tc in msg.tool_calls:
                        lines.append(f"        - {tc.name}")

            elif isinstance(msg, ToolResultMessage):
                lines.append(f"      Results: {len(msg.results)}")
                for result in msg.results:
                    text_count = sum(1 for c in result.content if hasattr(c, 'text'))
                    image_count = sum(1 for c in result.content if hasattr(c, 'data'))
                    lines.append(f"        - {result.name}: {text_count} text, {image_count} images")

        return "\n".join(lines)
