"""Utility tools for common actions."""

from dodo import tool
from webtask._internal.utils.wait import wait


@tool
class WaitTool:
    """Wait for specified seconds (useful after actions that trigger page changes, modals, or dynamic content loading)."""

    async def run(self, seconds: float) -> str:
        """
        Args:
            seconds: Seconds to wait (0.1 to 10)
        """
        # Clamp to valid range
        seconds = max(0.1, min(10.0, seconds))
        await wait(seconds)
        return f"Waited {seconds} seconds"
