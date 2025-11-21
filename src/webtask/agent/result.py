"""User-facing result classes for Agent methods."""

from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Result:
    """Result from agent.do() - always successful (throws on abort)."""

    output: Optional[Any] = None
    feedback: Optional[str] = None

    def __str__(self) -> str:
        return f"Result(output={self.output is not None}, feedback='{self.feedback}')"


@dataclass
class Verdict:
    """Result from agent.verify() - always successful (throws on abort)."""

    passed: bool
    feedback: str

    def __bool__(self) -> bool:
        """Allow using verdict in boolean context."""
        return self.passed

    def __eq__(self, other) -> bool:
        """Allow comparing verdict with boolean."""
        if isinstance(other, bool):
            return self.passed == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return f"Verdict(passed={self.passed}, feedback='{self.feedback}')"
