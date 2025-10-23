"""Wait utilities for async operations."""

import asyncio


async def wait(seconds: float) -> None:
    """
    Wait for a specified number of seconds.

    Simple async sleep utility for delaying execution.

    Args:
        seconds: Number of seconds to wait

    Example:
        >>> from webtask.utils import wait
        >>> await wait(2.0)  # Wait 2 seconds
    """
    await asyncio.sleep(seconds)
