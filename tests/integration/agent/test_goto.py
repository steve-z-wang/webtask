"""Integration tests for agent.goto() method."""

import pytest
from webtask import Webtask
from webtask.integrations.llm import Gemini
import os


@pytest.mark.integration
@pytest.mark.asyncio
async def test_goto_with_full_url():
    """Test goto() with full https:// URL."""
    wt = Webtask()
    llm = Gemini(model="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm, headless=True)

    await agent.goto("https://practicesoftwaretesting.com/")

    page = agent.get_current_page()
    assert page is not None
    assert "practicesoftwaretesting.com" in page.url

    await wt.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_goto_without_protocol():
    """Test goto() without protocol (should auto-add https://)."""
    wt = Webtask()
    llm = Gemini(model="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm, headless=True)

    await agent.goto("practicesoftwaretesting.com")

    page = agent.get_current_page()
    assert page is not None
    assert "practicesoftwaretesting.com" in page.url
    assert page.url.startswith("https://")

    await wt.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_goto_with_path():
    """Test goto() with domain and path."""
    wt = Webtask()
    llm = Gemini(model="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm, headless=True)

    await agent.goto("practicesoftwaretesting.com/#/")

    page = agent.get_current_page()
    assert page is not None
    assert "practicesoftwaretesting.com" in page.url

    await wt.close()
