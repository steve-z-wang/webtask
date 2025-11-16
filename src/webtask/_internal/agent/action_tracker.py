"""ActionTracker - tracks and summarizes worker actions."""

from typing import List, Dict, Any, Optional


class ActionTracker:
    """Tracks worker actions and provides formatted summaries."""

    def __init__(self):
        self.actions: List[Dict[str, Any]] = []

    def add_action(self, description: str, status: str, error: Optional[str] = None):
        action_record = {
            "description": description,
            "status": status,
        }
        if error:
            action_record["error"] = error

        self.actions.append(action_record)

    def get_summary_text(self, exclude_last_n: int = 0) -> str:
        """Get formatted summary, optionally excluding last N actions."""
        actions_to_summarize = (
            self.actions[:-exclude_last_n] if exclude_last_n > 0 else self.actions
        )

        if not actions_to_summarize:
            return "No previous actions."

        lines = []
        for i, action in enumerate(actions_to_summarize, 1):
            desc = action["description"]
            status = action["status"]

            if status == "error":
                error = action.get("error", "Unknown error")
                lines.append(f"{i}. {desc} (ERROR: {error})")
            else:
                lines.append(f"{i}. {desc}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ActionTracker(actions={len(self.actions)})"
