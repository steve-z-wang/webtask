"""SubtaskExecution - execution history for one subtask."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession

from .subtask import Subtask


@dataclass
class SubtaskExecution:
    """Execution history for one subtask (Worker/Verifier cycle)."""

    subtask: Subtask
    history: List[Union["WorkerSession", "VerifierSession"]] = field(
        default_factory=list
    )

    def add_session(self, session: Union["WorkerSession", "VerifierSession"]) -> None:
        """Add a Worker or Verifier session to history."""
        self.history.append(session)

    def get_correction_count(self) -> int:
        """Count how many times Verifier requested correction."""
        from .verifier.verifier_session import VerifierSession

        count = 0
        for session in self.history:
            if isinstance(session, VerifierSession):
                if (
                    session.subtask_decision
                    and session.subtask_decision.tool == "request_correction"
                ):
                    count += 1
        return count

    def __str__(self) -> str:
        lines = []
        lines.append(f"SubtaskExecution: {self.subtask.description}")
        lines.append(f"Status: {self.subtask.status.value}")
        lines.append(f"Sessions: {len(self.history)}")

        if self.history:
            lines.append("\nSession History:")
            for session in self.history:
                session_type = (
                    "Worker" if "Worker" in type(session).__name__ else "Verifier"
                )
                lines.append(f"\n[{session_type} Session {session.session_number}]")
                # Indent each line of the session details
                for line in str(session).split("\n"):
                    lines.append(f"  {line}")

        return "\n".join(lines)
