"""Simple demo for recording a video."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from webtask import Webtask
from webtask.integrations.llm import Gemini

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(record_video_dir="videos/")

        wt = Webtask()
        agent = wt.create_agent_with_context(
            llm=Gemini(model="gemini-2.5-flash"),
            context=context,
            wait_after_action=2.0,
        )

        await agent.goto("https://practicesoftwaretesting.com")
        await agent.wait(3)

        await agent.do("add 3 Flat-Head Wood Screws to the cart")

        await agent.wait(2)
        await context.close()  # Video saved on close
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
