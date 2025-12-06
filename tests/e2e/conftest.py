"""Pytest configuration for e2e tests."""

import os
from pathlib import Path
import pytest
from dotenv import load_dotenv
from webtask import Webtask
from webtask.integrations.llm import Gemini

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@pytest.fixture
async def webtask():
    """Create and cleanup Webtask instance."""
    wt = Webtask()
    yield wt
    await wt.close()


@pytest.fixture
def llm():
    """Create Gemini LLM instance."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    return Gemini(model="gemini-2.5-flash", api_key=api_key)


@pytest.fixture
async def agent(webtask: Webtask, llm: Gemini):
    """Create agent for test."""
    return await webtask.create_agent(llm=llm, headless=False, wait_after_action=3.0)
