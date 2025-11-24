"""Tests for UploadTool with FileManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from webtask._internal.agent.tools import UploadTool
from webtask._internal.agent.file_manager import FileManager

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_browser():
    """Create a mock browser."""
    browser = MagicMock()
    mock_element = MagicMock()
    mock_element.upload_file = AsyncMock()
    browser.select = AsyncMock(return_value=mock_element)
    browser.wait = AsyncMock()
    return browser


class TestUploadTool:
    """Tests for UploadTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_single_file(self, mock_browser):
        """Test uploading a single file by index."""
        files = ["/path/to/photo.jpg", "/path/to/doc.pdf"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm)

        result = await tool.run(
            element_id="[input-0]",
            file_indexes=[0],
            description="Profile photo upload",
        )

        mock_browser.select.assert_called_once_with("[input-0]")
        element = await mock_browser.select("[input-0]")
        element.upload_file.assert_called_with("/path/to/photo.jpg")
        assert "Uploaded files [0]" in result
        assert "Profile photo upload" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_multiple_files(self, mock_browser):
        """Test uploading multiple files by indexes."""
        files = ["/path/to/photo1.jpg", "/path/to/photo2.jpg", "/path/to/photo3.jpg"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm)

        result = await tool.run(
            element_id="[input-0]",
            file_indexes=[0, 2],
            description="Photo gallery upload",
        )

        mock_browser.select.assert_called_once_with("[input-0]")
        element = await mock_browser.select("[input-0]")
        element.upload_file.assert_called_with(
            ["/path/to/photo1.jpg", "/path/to/photo3.jpg"]
        )
        assert "[0]" in result
        assert "[2]" in result
        assert "Photo gallery upload" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_invalid_index_raises_error(self, mock_browser):
        """Test that invalid file index raises ValueError."""
        fm = FileManager(["/path/to/file.jpg"])
        tool = UploadTool(mock_browser, fm)

        with pytest.raises(ValueError, match="File index 5 out of range"):
            await tool.run(
                element_id="[input-0]",
                file_indexes=[5],  # Out of range
                description="Upload",
            )
