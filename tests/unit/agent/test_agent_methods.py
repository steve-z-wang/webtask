"""Unit tests for Agent convenience methods."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from webtask.agent import Agent
from webtask.browser import Context


@pytest.mark.unit
@pytest.mark.asyncio
async def test_screenshot_saves_to_file(mocker):
    """Test that screenshot() calls page.screenshot() with correct params."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)
    mock_page = AsyncMock()
    mock_page.screenshot = AsyncMock(return_value=b"fake_image_data")

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock get_current_page to return our mock page
    mocker.patch.object(agent, "get_current_page", return_value=mock_page)

    # Call screenshot
    result = await agent.screenshot("test.png")

    # Verify
    assert result == b"fake_image_data"
    mock_page.screenshot.assert_called_once_with(path="test.png", full_page=False)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_screenshot_full_page(mocker):
    """Test that screenshot() with full_page=True passes it correctly."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)
    mock_page = AsyncMock()
    mock_page.screenshot = AsyncMock(return_value=b"fake_image_data")

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock get_current_page to return our mock page
    mocker.patch.object(agent, "get_current_page", return_value=mock_page)

    # Call screenshot with full_page
    result = await agent.screenshot("test.png", full_page=True)

    # Verify
    assert result == b"fake_image_data"
    mock_page.screenshot.assert_called_once_with(path="test.png", full_page=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_screenshot_without_path(mocker):
    """Test that screenshot() without path returns bytes without saving."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)
    mock_page = AsyncMock()
    mock_page.screenshot = AsyncMock(return_value=b"fake_image_data")

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock get_current_page to return our mock page
    mocker.patch.object(agent, "get_current_page", return_value=mock_page)

    # Call screenshot without path
    result = await agent.screenshot()

    # Verify
    assert result == b"fake_image_data"
    mock_page.screenshot.assert_called_once_with(path=None, full_page=False)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_screenshot_raises_when_no_page(mocker):
    """Test that screenshot() raises RuntimeError when no page is active."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock get_current_page to return None
    mocker.patch.object(agent, "get_current_page", return_value=None)

    # Verify it raises
    with pytest.raises(RuntimeError, match="No active page"):
        await agent.screenshot()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wait():
    """Test that wait() calls the internal wait utility."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock the internal wait utility
    with patch("webtask._internal.utils.wait.wait") as mock_wait:
        mock_wait.return_value = None

        # Call wait
        await agent.wait(2.5)

        # Verify internal wait was called with correct duration
        mock_wait.assert_called_once_with(2.5)
