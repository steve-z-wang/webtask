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
    browser.upload = AsyncMock()
    return browser


class TestUploadTool:
    """Tests for UploadTool."""

    @pytest.mark.unit
    def test_is_enabled_with_files(self, mock_browser):
        """Test tool is enabled when files are provided."""
        fm = FileManager(["/path/to/file.jpg"])
        tool = UploadTool(mock_browser, fm)
        assert tool.is_enabled() is True

    @pytest.mark.unit
    def test_is_disabled_without_files(self, mock_browser):
        """Test tool is disabled when no files are provided."""
        fm = FileManager(None)
        tool = UploadTool(mock_browser, fm)
        assert tool.is_enabled() is False

    @pytest.mark.unit
    def test_is_disabled_with_empty_files(self, mock_browser):
        """Test tool is disabled when files list is empty."""
        fm = FileManager([])
        tool = UploadTool(mock_browser, fm)
        assert tool.is_enabled() is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_single_file(self, mock_browser):
        """Test uploading a single file by index."""
        files = ["/path/to/photo.jpg", "/path/to/doc.pdf"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0],
            description="Profile photo upload",
        )

        await tool.execute(params)

        mock_browser.upload.assert_called_once_with("[input-0]", "/path/to/photo.jpg")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_multiple_files(self, mock_browser):
        """Test uploading multiple files by indexes."""
        files = ["/path/to/photo1.jpg", "/path/to/photo2.jpg", "/path/to/photo3.jpg"]
        fm = FileManager(files)
        tool = UploadTool(mock_browser, fm)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0, 2],
            description="Photo gallery upload",
        )

        await tool.execute(params)

        mock_browser.upload.assert_called_once_with(
            "[input-0]", ["/path/to/photo1.jpg", "/path/to/photo3.jpg"]
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_invalid_index_raises_error(self, mock_browser):
        """Test that invalid file index raises ValueError."""
        fm = FileManager(["/path/to/file.jpg"])
        tool = UploadTool(mock_browser, fm)

        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[5],  # Out of range
            description="Upload",
        )

        with pytest.raises(ValueError, match="File index 5 out of range"):
            await tool.execute(params)

    @pytest.mark.unit
    def test_describe_single_file(self):
        """Test description generation for single file."""
        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0],
            description="Profile photo",
        )

        desc = UploadTool.describe(params)
        assert desc == "Uploaded files [0] to Profile photo"

    @pytest.mark.unit
    def test_describe_multiple_files(self):
        """Test description generation for multiple files."""
        params = UploadTool.Params(
            element_id="[input-0]",
            file_indexes=[0, 1, 2],
            description="Photo gallery",
        )

        desc = UploadTool.describe(params)
        assert desc == "Uploaded files [0], [1], [2] to Photo gallery"
