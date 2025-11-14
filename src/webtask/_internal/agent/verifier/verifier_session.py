"""VerifierSession - tracks one verifier.run() execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from webtask.llm import (
    Message,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    TextContent,
    ImageContent,
)


class VerifierDecision(str, Enum):
    """Verifier decision about task completion."""

    COMPLETE_TASK = "complete_task"
    REQUEST_CORRECTION = "request_correction"
    ABORT_TASK = "abort_task"


@dataclass
class VerifierSession:
    """Verifier session with conversation history."""

    task_description: str
    decision: VerifierDecision
    feedback: str
    start_time: datetime
    end_time: datetime
    max_steps: int = 5
    steps_used: int = 0
    messages: List[Message] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Generate comprehensive summary showing all conversation details."""
        lines = ["=" * 80]
        lines.append("VERIFIER SESSION SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Task: {self.task_description}")
        lines.append(f"Steps: {self.steps_used}/{self.max_steps}")
        lines.append(f"Decision: {self.decision}")
        lines.append(f"Feedback: {self.feedback}")
        duration = (self.end_time - self.start_time).total_seconds()
        lines.append(
            f"Duration: {duration:.2f}s ({self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')})"
        )
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
                        lines.append(
                            f"  [{j}] Image: {part.mime_type.value}, {len(part.data)} bytes"
                        )

            elif isinstance(msg, AssistantMessage):
                # Show tool calls
                if msg.tool_calls:
                    lines.append(f"Tool Calls: {len(msg.tool_calls)}")
                    for j, tc in enumerate(msg.tool_calls, 1):
                        lines.append(f"  [{j}] {tc.name}")
                        for key, value in tc.arguments.items():
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

                # Show page state
                text_parts = [p for p in msg.content if isinstance(p, TextContent)]
                image_parts = [p for p in msg.content if isinstance(p, ImageContent)]

                lines.append("Page State:")
                if text_parts:
                    lines.append(
                        f"  DOM Snapshot: {len(text_parts)} text part(s) (hidden for brevity)"
                    )
                if image_parts:
                    lines.append(f"  Screenshots: {len(image_parts)} image(s)")

            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"VerifierSession(steps={self.steps_used}/{self.max_steps}, decision={self.decision}, messages={len(self.messages)})"
