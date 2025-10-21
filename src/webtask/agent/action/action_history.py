"""Action history - maintains record of executed actions."""

from typing import List
from .action import Action


class ActionHistory:
    """
    Maintains history of executed actions.
    """

    def __init__(self):
        """Initialize empty action history."""
        self._actions: List[Action] = []

    def add(self, action: Action) -> None:
        """
        Add an action to the history.

        Args:
            action: Action that was executed
        """
        self._actions.append(action)

    def clear(self) -> None:
        """Clear all actions from history."""
        self._actions.clear()

    def get_all(self) -> List[Action]:
        """
        Get all actions in history.

        Returns:
            List of all executed actions
        """
        return list(self._actions)
