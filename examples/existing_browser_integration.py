"""
Example: Using Agent with an existing Playwright browser/page.

This example shows how to integrate Webtask Agent with your existing
Playwright browser setup.
"""

import asyncio
from playwright.async_api import async_playwright

# Webtask imports
from webtask import Agent
from webtask.integrations.llm import GeminiLLM
from webtask.integrations.browser.playwright import PlaywrightPage


async def example_1_inject_existing_page():
    """Example 1: Inject your existing Playwright page into the agent."""
    print("\n=== Example 1: Inject Existing Page ===")

    # Your existing Playwright setup
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to a page (your existing workflow)
    await page.goto("https://www.google.com")

    # Now inject your page into Webtask Agent
    print("Creating agent with existing Playwright page...")

    # Wrap the Playwright page
    wrapped_page = PlaywrightPage(page)

    # Create agent with the page
    llm = GeminiLLM.create(model="gemini-2.0-flash-exp")
    agent = Agent(llm, page=wrapped_page)

    # Now use the agent on your existing page!
    print("Executing task on existing page...")
    result = await agent.execute("search for 'anthropic' and click search")

    print(f"Task completed: {result.completed}")
    print(f"Steps taken: {len(result.steps)}")

    # The agent worked on YOUR page, not a new one
    print(f"Current URL: {page.url}")

    # Cleanup
    await agent.close()
    await browser.close()
    await playwright.stop()


async def example_2_set_page_later():
    """Example 2: Create agent first, set page later."""
    print("\n=== Example 2: Set Page Later ===")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await (await browser.new_context()).new_page()

    # Create agent first (empty)
    llm = GeminiLLM.create(model="gemini-2.0-flash-exp")
    agent = Agent(llm)  # No session, no page yet

    # Navigate with your existing code
    await page.goto("https://github.com")

    # Later: inject the page using set_page()
    wrapped_page = PlaywrightPage(page)
    agent.set_page(wrapped_page)

    # Now use the agent
    print("Executing task...")
    await agent.execute("find the search button")

    # Cleanup
    await browser.close()
    await playwright.stop()


async def example_3_multi_page_management():
    """Example 3: Manage multiple pages with set_page()."""
    print("\n=== Example 3: Multi-Page Management ===")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)

    # Create multiple pages
    page1 = await (await browser.new_context()).new_page()
    page2 = await (await browser.new_context()).new_page()

    await page1.goto("https://google.com")
    await page2.goto("https://github.com")

    # Create agent
    llm = GeminiLLM.create(model="gemini-2.0-flash-exp")
    agent = Agent(llm)

    # Work on page 1
    wrapped_page1 = PlaywrightPage(page1)
    agent.set_page(wrapped_page1)
    print("Working on Google...")
    await agent.execute("search for 'AI'")

    # Switch to page 2
    wrapped_page2 = PlaywrightPage(page2)
    agent.set_page(wrapped_page2)
    print("Switching to GitHub...")
    await agent.execute("click the search button")

    # Switch back to page 1
    agent.set_page(wrapped_page1)
    print("Back to Google...")

    # Check managed pages
    pages = agent.get_pages()
    print(f"Total pages managed: {agent.page_count}")

    # Cleanup
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_1_inject_existing_page())
    # asyncio.run(example_2_set_page_later())
    # asyncio.run(example_3_multi_page_management())
