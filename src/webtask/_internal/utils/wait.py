
import asyncio


async def wait(seconds: float) -> None:
    await asyncio.sleep(seconds)
