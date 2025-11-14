"""WorkerSession - tracks one worker.run() execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
)


class WorkerEndReason(str, Enum):
    """Worker execution end reason."""

    COMPLETE_WORK = "complete_work"
    ABORT_WORK = "abort_work"
    MAX_STEPS = "max_steps"


@dataclass
class WorkerSession:
    """Worker session with conversation history."""

    task_description: str
    start_time: datetime
    end_time: datetime
    max_steps: int = 20
    steps_used: int = 0
    end_reason: Optional[WorkerEndReason] = None
    messages: List[Message] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Generate comprehensive summary showing all conversation details recursively."""
        lines = ["=" * 80]
        lines.append("WORKER SESSION SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Task: {self.task_description}")
        lines.append(f"Steps: {self.steps_used}/{self.max_steps}")
        lines.append(f"End Reason: {self.end_reason}")
        duration = (self.end_time - self.start_time).total_seconds()
        lines.append(f"Duration: {duration:.2f}s ({self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')})")
        lines.append("")

        # Show each message with full details
        for i, msg in enumerate(self.messages, 1):
            lines.append(f"{'─' * 80}")
            lines.append(f"Message {i}: {msg.__class__.__name__}")
            lines.append(f"{'─' * 80}")

            if isinstance(msg, SystemMessage):
                lines.append("Content:")
                for j, part in enumerate(msg.content, 1):
                    text = part.text
                    # Truncate very long system messages
                    if len(text) > 500:
                        text = text[:500] + "..."
                    lines.append(f"  [{j}] Text: {text}")

            elif isinstance(msg, UserMessage):
                lines.append("Content:")
                for j, part in enumerate(msg.content, 1):
                    if isinstance(part, TextContent):
                        text = part.text
                        if len(text) > 300:
                            text = text[:300] + "..."
                        lines.append(f"  [{j}] Text: {text}")
                    elif isinstance(part, ImageContent):
                        lines.append(f"  [{j}] Image: {part.mime_type.value}, {len(part.data)} bytes")

            elif isinstance(msg, AssistantMessage):
                # Show content if present
                if msg.content:
                    lines.append("Content:")
                    for j, part in enumerate(msg.content, 1):
                        if isinstance(part, TextContent):
                            lines.append(f"  [{j}] Text: {part.text}")
                        elif isinstance(part, ImageContent):
                            lines.append(f"  [{j}] Image: {part.mime_type.value}")

                # Show tool calls
                if msg.tool_calls:
                    lines.append(f"Tool Calls: {len(msg.tool_calls)}")
                    for j, tc in enumerate(msg.tool_calls, 1):
                        lines.append(f"  [{j}] {tc.name}")
                        for key, value in tc.arguments.items():
                            # Truncate long argument values
                            value_str = str(value)
                            if len(value_str) > 200:
                                value_str = value_str[:200] + "..."
                            lines.append(f"      {key}: {value_str}")

            elif isinstance(msg, ToolResultMessage):
                # Show results
                lines.append(f"Results: {len(msg.results)}")
                for j, result in enumerate(msg.results, 1):
                    status_str = f"{result.name}: {result.status.value}"
                    if result.output is not None:
                        output_str = str(result.output)
                        if len(output_str) > 100:
                            output_str = output_str[:100] + "..."
                        status_str += f" -> {output_str}"
                    if result.error:
                        status_str += f" (error: {result.error})"
                    lines.append(f"  [{j}] {status_str}")

                # Show page state content (without DOM text which is too verbose)
                text_parts = [p for p in msg.content if isinstance(p, TextContent)]
                image_parts = [p for p in msg.content if isinstance(p, ImageContent)]

                lines.append("Page State:")
                if text_parts:
                    lines.append(f"  DOM Snapshot: {len(text_parts)} text part(s) (hidden for brevity)")

                if image_parts:
                    lines.append(f"  Screenshots: {len(image_parts)} image(s)")
                    for j, part in enumerate(image_parts, 1):
                        lines.append(f"    [{j}] {part.mime_type.value}, {len(part.data)} bytes")

            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"WorkerSession(task='{self.task_description}', steps={self.steps_used}/{self.max_steps}, end_reason={self.end_reason}, messages={len(self.messages)})"
