"""Throttler - manages delays between operations."""

import time
from typing import Optional
from ..utils import wait


class Throttler:
    """
    Manages delays between operations to prevent overwhelming the browser/API.

    Ensures a minimum delay between any operations (LLM calls, browser actions, etc.)
    by tracking the last operation time and waiting if needed.
    """

    def __init__(self, delay: float = 1.0):
        """
        Initialize Throttler.

        Args:
            delay: Minimum delay in seconds between operations
        """
        self.delay = delay
        self.last_operation_time: Optional[float] = None

    async def wait_if_needed(self):
        """
        Wait if needed to maintain minimum delay between operations.

        Call this before or after each operation to ensure proper spacing.
        Automatically tracks timing and waits only the remaining time needed.
        """
        if self.last_operation_time is not None:
            elapsed = time.time() - self.last_operation_time
            if elapsed < self.delay:
                await wait(self.delay - elapsed)

        self.last_operation_time = time.time()
