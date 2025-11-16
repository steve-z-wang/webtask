"""E2E test for tool website shopping cart automation.

Based on examples/tool_website_demo.ipynb

This test demonstrates the recording/replay pattern with a real automation task:
- Navigate to practicesoftwaretesting.com
- Add items to shopping cart
- Verify cart contents

Usage:
    # Record interactions (run once)
    WEBTASK_TEST_MODE=record pytest tests/e2e/test_tool_website.py -v

    # Replay interactions (fast, offline, deterministic)
    WEBTASK_TEST_MODE=replay pytest tests/e2e/test_tool_website.py -v

    # Live mode (normal operation)
    pytest tests/e2e/test_tool_website.py -v
"""

import pytest
import os
from dotenv import load_dotenv
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM
from webtask.integrations.browser.playwright import PlaywrightBrowser
from webtask.testing import RecordingLLM, RecordingBrowser
from webtask._internal.config import Config

# Load environment variables from .env file
load_dotenv()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_shopping_cart_automation():
    """Test automated shopping cart interaction with recording/replay.

    This test:
    1. Navigates to the practice software testing website
    2. Uses agent to add specific items to cart
    3. Verifies the task completed successfully
    """

    # Auto-detect headless mode: show browser when recording, headless otherwise
    config = Config()
    headless = not config.is_recording()  # False when recording, True otherwise

    # Clean up fixtures before recording
    from pathlib import Path
    import shutil

    fixture_path = Path("tests/e2e/fixtures/shopping_cart/")

    if config.is_recording() and fixture_path.exists():
        shutil.rmtree(fixture_path)

    # Auto-discover instance IDs from fixtures during replay
    llm_instance_id = None
    browser_instance_id = None
    if config.is_replaying():
        # Find llm_{uuid} directory
        llm_dirs = list(fixture_path.glob("llm_*"))
        if llm_dirs:
            llm_instance_id = llm_dirs[0].name.replace("llm_", "")

        # Find browser_{uuid} directory
        browser_dirs = list(fixture_path.glob("browser_*"))
        if browser_dirs:
            browser_instance_id = browser_dirs[0].name.replace("browser_", "")

    # Setup LLM with recording
    api_key = os.getenv("GOOGLE_API_KEY")
    base_llm = (
        GeminiLLM.create(model="gemini-2.5-flash", api_key=api_key)
        if not config.is_replaying()
        else None
    )
    llm = RecordingLLM(
        llm=base_llm, fixture_path=str(fixture_path), instance_id=llm_instance_id
    )

    # Setup Browser with recording (same fixture path!)
    base_browser = (
        await PlaywrightBrowser.create(headless=headless)
        if not config.is_replaying()
        else None
    )
    browser = RecordingBrowser(
        browser=base_browser,
        fixture_path=str(fixture_path),
        instance_id=browser_instance_id,
    )

    # Create Webtask
    wt = Webtask(headless=True)

    try:
        # Create agent with recording wrappers
        agent = await wt.create_agent_with_browser(
            llm=llm, browser=browser, use_screenshot=True
        )

        # Navigate to the starting page
        await agent.navigate("https://practicesoftwaretesting.com/")
        await agent.wait_for_idle()

        # Execute the shopping cart task
        result = await agent.execute(
            "add 2 Flat-Head Wood Screws and 5 cross-head screws to the cart, and proceed to the cart",
        )

        # Verify task completed successfully
        assert result is not None

        # The task should have completed (not aborted)
        print(f"\nTask Result: {result.result}")
        print(f"Number of sessions: {len(result.sessions)}")
        print(f"Feedback: {result.feedback}")

        # Verify task completed (not aborted)
        from webtask._internal.agent.task_execution import TaskResult

        assert (
            result.result == TaskResult.COMPLETE
        ), f"Task should have completed successfully, but result is {result.result}"

    finally:
        # Cleanup
        await browser.close()
