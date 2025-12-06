"""Tests for UploadTool with FileManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from webtask._internal.agent.tools import UploadTool
from webtask._internal.agent.file_manager import FileManager
from webtask.llm.message import ToolResultStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_browser():
    """Create a mock browser."""
    browser = MagicMock()
    mock_element = MagicMock()
    mock_element.upload_file = AsyncMock()
    browser.select = AsyncMock(return_value=mock_element)
    return browser


class TestUploadTool:
    """Tests for UploadTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_single_file(self, mock_browser):
        """Test uploading a single file by index."""
        files = ["/path/to/photo.jpg", "/path/to/doc.pdf"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm, wait_after_action=0.0)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0],
            description="Profile photo upload",
        )

        result = await tool.execute(params)

        mock_browser.select.assert_called_once_with("[input-0]")
        element = await mock_browser.select("[input-0]")
        element.upload_file.assert_called_with("/path/to/photo.jpg")
        assert result.status == ToolResultStatus.SUCCESS
        assert "Uploaded files [0]" in result.description
        assert "Profile photo upload" in result.description

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_multiple_files(self, mock_browser):
        """Test uploading multiple files by indexes."""
        files = ["/path/to/photo1.jpg", "/path/to/photo2.jpg", "/path/to/photo3.jpg"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm, wait_after_action=0.0)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0, 2],
            description="Photo gallery upload",
        )

        result = await tool.execute(params)

        mock_browser.select.assert_called_once_with("[input-0]")
        element = await mock_browser.select("[input-0]")
        element.upload_file.assert_called_with(
            ["/path/to/photo1.jpg", "/path/to/photo3.jpg"]
        )
        assert result.status == ToolResultStatus.SUCCESS
        assert "[0]" in result.description
        assert "[2]" in result.description
        assert "Photo gallery upload" in result.description

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_invalid_index_raises_error(self, mock_browser):
        """Test that invalid file index raises ValueError."""
        fm = FileManager(["/path/to/file.jpg"])
        tool = UploadTool(mock_browser, fm, wait_after_action=0.0)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[5],  # Out of range
            description="Upload",
        )

        with pytest.raises(ValueError, match="File index 5 out of range"):
            await tool.execute(params)
