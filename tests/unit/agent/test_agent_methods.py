"""Unit tests for Agent convenience methods."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from webtask.agent import Agent
from webtask.browser import Context
from webtask._internal.agent.run import Run, TaskResult, TaskStatus
from webtask._internal.agent.task_runner import TaskRunner
from webtask.exceptions import (
    TaskAbortedError,
    VerificationAbortedError,
    ExtractionAbortedError,
)


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
async def test_wait(mocker):
    """Test that wait() calls asyncio.sleep with correct duration."""
    # Mock dependencies
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    # Create agent
    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock asyncio.sleep which is called by the wait utility
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    # Call wait
    await agent.wait(2.5)

    # Verify asyncio.sleep was called with correct duration
    mock_sleep.assert_called_once_with(2.5)


# Tests for throw-on-abort behavior


@pytest.mark.unit
@pytest.mark.asyncio
async def test_do_throws_on_abort(mocker):
    """Test that do() throws TaskAbortedError when task is aborted."""
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock TaskRunner.run to return aborted result
    mock_run = Run(
        result=TaskResult(
            status=TaskStatus.ABORTED, feedback="Could not complete task"
        ),
        summary="",
        messages=[],
        task_description="test task",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        with pytest.raises(TaskAbortedError, match="Could not complete task"):
            await agent.do("test task")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_do_returns_result_on_success(mocker):
    """Test that do() returns Result when task completes."""
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock TaskRunner.run to return completed result
    mock_run = Run(
        result=TaskResult(
            status=TaskStatus.COMPLETED,
            feedback="Task completed successfully",
            output={"key": "value"},
        ),
        summary="",
        messages=[],
        task_description="test task",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        result = await agent.do("test task")

        assert result.feedback == "Task completed successfully"
        assert result.output == {"key": "value"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_throws_on_abort(mocker):
    """Test that verify() throws VerificationAbortedError when verification is aborted."""
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock TaskRunner.run to return aborted result
    mock_run = Run(
        result=TaskResult(status=TaskStatus.ABORTED, feedback="Could not verify"),
        summary="",
        messages=[],
        task_description="test",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        with pytest.raises(VerificationAbortedError, match="Could not verify"):
            await agent.verify("cart has 7 items")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_returns_verdict_on_success(mocker):
    """Test that verify() returns Verdict when verification completes."""

    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Create mock output matching VerificationResult schema
    class MockVerificationResult:
        verified = True

    mock_run = Run(
        result=TaskResult(
            status=TaskStatus.COMPLETED,
            feedback="Condition is true",
            output=MockVerificationResult(),
        ),
        summary="",
        messages=[],
        task_description="test",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        verdict = await agent.verify("cart has 7 items")

        assert verdict.passed is True
        assert verdict.feedback == "Condition is true"
        assert bool(verdict) is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_throws_on_abort(mocker):
    """Test that extract() throws ExtractionAbortedError when extraction is aborted."""
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Mock TaskRunner.run to return aborted result
    mock_run = Run(
        result=TaskResult(status=TaskStatus.ABORTED, feedback="Could not extract"),
        summary="",
        messages=[],
        task_description="test",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        with pytest.raises(ExtractionAbortedError, match="Could not extract"):
            await agent.extract("total price")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_returns_string_on_success(mocker):
    """Test that extract() returns string when no schema provided."""
    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Create mock output matching default StrOutput schema
    class MockStrOutput:
        value = "$99.99"

    mock_run = Run(
        result=TaskResult(
            status=TaskStatus.COMPLETED,
            feedback="Extracted price",
            output=MockStrOutput(),
        ),
        summary="",
        messages=[],
        task_description="test",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        result = await agent.extract("total price")

        assert result == "$99.99"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_returns_structured_output_with_schema(mocker):
    """Test that extract() returns structured output when schema provided."""
    from pydantic import BaseModel

    class ProductInfo(BaseModel):
        name: str
        price: float

    mock_llm = Mock()
    mock_context = Mock(spec=Context)

    agent = Agent(llm=mock_llm, context=mock_context)

    # Create mock output matching provided schema
    mock_output = ProductInfo(name="Widget", price=29.99)

    mock_run = Run(
        result=TaskResult(
            status=TaskStatus.COMPLETED,
            feedback="Extracted product info",
            output=mock_output,
        ),
        summary="",
        messages=[],
        task_description="test",
        steps_used=1,
        max_steps=10,
    )

    with patch.object(TaskRunner, "run", new_callable=AsyncMock) as mock_task_run:
        mock_task_run.return_value = mock_run

        result = await agent.extract("product info", ProductInfo)

        assert isinstance(result, ProductInfo)
        assert result.name == "Widget"
        assert result.price == 29.99
