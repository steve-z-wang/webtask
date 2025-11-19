"""Testing utilities for webtask.

This module provides recording and replay capabilities for deterministic testing
of web automation scripts.

Example:
    from webtask.testing import RecordingLLM, RecordingBrowser
    from webtask.integrations.llm import GeminiLLM
    from webtask.integrations.browser.playwright import PlaywrightBrowser

    # Record mode (WEBTASK_TEST_MODE=record)
    base_llm = GeminiLLM.create(...)
    llm = RecordingLLM(llm=base_llm, fixture_path="fixtures/llm/test/")

    base_browser = await PlaywrightBrowser.create(...)
    browser = RecordingBrowser(browser=base_browser, fixture_path="fixtures/browser/test/")

    # Replay mode (WEBTASK_TEST_MODE=replay)
    # Same code works - automatically uses recorded data!
"""

from .recording_llm import RecordingLLM
from .recording_browser import (
    RecordingBrowser,
    RecordingContext,
    RecordingPage,
    RecordingElement,
)

__all__ = [
    "RecordingLLM",
    "RecordingBrowser",
    "RecordingContext",
    "RecordingPage",
    "RecordingElement",
]
