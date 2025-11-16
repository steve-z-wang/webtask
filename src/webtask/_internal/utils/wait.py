"""Wait utilities for async operations."""

import asyncio
from webtask._internal.config import Config


async def wait(seconds: float) -> None:
    """Wait for a specified number of seconds.

    In replay mode, skips waiting for faster tests.
    """
    # Skip waiting in replay mode for faster tests
    if Config().is_replaying():
        return

    await asyncio.sleep(seconds)
