"""Tests for AgentBrowser tab management methods."""

import pytest
from unittest.mock import MagicMock

from webtask._internal.agent.agent_browser import AgentBrowser
from webtask.browser import Page

pytestmark = pytest.mark.unit


class MockPage(Page):
    """Mock Page that inherits from Page base class."""

    def __init__(self, url="https://example.com"):
        self._url = url
        self._closed = False

    def __eq__(self, other):
        if not isinstance(other, MockPage):
            return False
        return self._url == other._url and id(self) == id(other)

    def __hash__(self):
        return hash(id(self))

    @property
    def context(self):
        return None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    async def close(self):
        self._closed = True

    async def goto(self, url):
        self._url = url

    async def get_cdp_dom_snapshot(self):
        return {}

    async def get_cdp_accessibility_tree(self):
        return {}

    async def select(self, selector):
        return []

    async def select_one(self, selector):
        raise ValueError("No elements found")

    async def wait_for_load(self, timeout=10000):
        pass

    async def screenshot(self, path=None, full_page=False):
        return b""

    async def keyboard_type(self, text, clear=False, delay=80):
        pass

    async def evaluate(self, script):
        return None

    def viewport_size(self):
        return (1280, 720)

    async def mouse_click(self, x, y):
        pass

    async def mouse_move(self, x, y):
        pass

    async def mouse_wheel(self, x, y, delta_x, delta_y):
        pass

    async def mouse_drag(self, x, y, dest_x, dest_y):
        pass

    async def keyboard_press(self, key):
        pass

    async def go_back(self):
        pass

    async def go_forward(self):
        pass


@pytest.fixture
def mock_page_factory():
    """Factory to create multiple mock pages with different URLs."""

    def create(url="https://example.com"):
        return MockPage(url)

    return create


@pytest.fixture
def mock_context(mock_page_factory):
    """Create a mock context."""
    context = MagicMock()
    context.pages = []

    async def create_page():
        page = mock_page_factory("about:blank")
        context.pages.append(page)
        return page

    context.create_page = create_page
    return context


@pytest.fixture
def browser(mock_context):
    """Create an AgentBrowser with mock context."""
    return AgentBrowser(context=mock_context)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_open_tab(browser, mock_context):
    """Test opening a new tab adds it to list and focuses it."""
    # Open a tab
    page = await browser.open_tab()

    # Verify tab is added to internal list
    assert len(browser._pages) == 1
    assert browser._pages[0] == page

    # Verify tab is focused (current)
    assert browser._current_page_index == 0
    assert browser.get_current_page() == page


@pytest.mark.asyncio
@pytest.mark.unit
async def test_focus_tab_by_index(browser, mock_context):
    """Test focusing a tab by 0-based index."""
    # Open two tabs
    page1 = await browser.open_tab()
    page1.url = "https://page1.com"
    page2 = await browser.open_tab()
    page2.url = "https://page2.com"

    # Current should be page2 (last opened)
    assert browser.get_current_page() == page2

    # Focus tab 0 by index
    browser.focus_tab(0)

    # Verify page1 is now current
    assert browser.get_current_page() == page1
    assert browser._current_page_index == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_focus_tab_by_reference(browser, mock_context):
    """Test focusing a tab by Page object reference."""
    # Open two tabs
    page1 = await browser.open_tab()
    page1.url = "https://page1.com"
    page2 = await browser.open_tab()
    page2.url = "https://page2.com"

    # Current should be page2 (last opened)
    assert browser.get_current_page() == page2

    # Focus page1 by reference
    browser.focus_tab(page1)

    # Verify page1 is now current
    assert browser.get_current_page() == page1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_tabs_context(browser, mock_context):
    """Test get_tabs_context returns formatted tabs with current marker."""
    # Open two tabs with different URLs
    page1 = await browser.open_tab()
    page1.url = "https://google.com"
    page2 = await browser.open_tab()
    page2.url = "https://github.com"

    # Get tabs context (page2 is current)
    tabs_context = browser._get_tabs_context()

    # Verify format
    assert "Tabs:" in tabs_context
    assert "- [0] https://google.com" in tabs_context
    assert "- [1] https://github.com (current)" in tabs_context

    # Focus tab 0 and verify marker moves
    browser.focus_tab(0)
    tabs_context = browser._get_tabs_context()

    assert "- [0] https://google.com (current)" in tabs_context
    assert "- [1] https://github.com" in tabs_context
    assert "(current)" not in tabs_context.split("\n")[2]  # tab 1 line


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sync_pages_detects_new_tab(browser, mock_context, mock_page_factory):
    """Test _sync_pages detects tabs opened externally."""
    # Open a tab through browser
    page1 = await browser.open_tab()
    page1.url = "https://page1.com"

    assert len(browser._pages) == 1

    # Simulate external tab creation (e.g., popup from click)
    external_page = mock_page_factory("https://popup.com")
    mock_context.pages.append(external_page)

    # Sync should detect the new tab
    browser._sync_pages()

    # Verify new tab is added
    assert len(browser._pages) == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sync_pages_removes_closed_tab(browser, mock_context):
    """Test _sync_pages removes tabs closed externally."""
    # Open two tabs
    page1 = await browser.open_tab()
    page1.url = "https://page1.com"
    page2 = await browser.open_tab()
    page2.url = "https://page2.com"

    assert len(browser._pages) == 2

    # Simulate external tab close (remove from context.pages)
    mock_context.pages.remove(page2)

    # Sync should detect the closed tab
    browser._sync_pages()

    # Verify closed tab is removed
    assert len(browser._pages) == 1
    assert page2 not in browser._pages
    assert page1 in browser._pages
