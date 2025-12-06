"""Wait utilities for async operations."""

import asyncio


async def wait(seconds: float) -> None:
    """Wait for a specified number of seconds."""
    await asyncio.sleep(seconds)
