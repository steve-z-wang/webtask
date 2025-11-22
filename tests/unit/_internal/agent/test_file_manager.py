"""Tests for FileManager."""

import pytest

from webtask._internal.agent.file_manager import FileManager

pytestmark = pytest.mark.unit


class TestFileManager:
    """Tests for FileManager."""

    @pytest.mark.unit
    def test_is_empty_with_no_files(self):
        """Test is_empty returns True when no files provided."""
        fm = FileManager(None)
        assert fm.is_empty() is True

        fm = FileManager([])
        assert fm.is_empty() is True

    @pytest.mark.unit
    def test_is_empty_with_files(self):
        """Test is_empty returns False when files are provided."""
        fm = FileManager(["/path/to/file.jpg"])
        assert fm.is_empty() is False

    @pytest.mark.unit
    def test_get_path_valid_index(self):
        """Test getting path by valid index."""
        files = ["/path/to/file1.jpg", "/path/to/file2.pdf"]
        fm = FileManager(files)

        assert fm.get_path(0) == "/path/to/file1.jpg"
        assert fm.get_path(1) == "/path/to/file2.pdf"

    @pytest.mark.unit
    def test_get_path_invalid_index_raises_error(self):
        """Test getting path by invalid index raises ValueError."""
        fm = FileManager(["/path/to/file.jpg"])

        with pytest.raises(ValueError, match="File index 5 out of range"):
            fm.get_path(5)

        with pytest.raises(ValueError, match="File index -1 out of range"):
            fm.get_path(-1)

    @pytest.mark.unit
    def test_get_paths_valid_indexes(self):
        """Test getting multiple paths by valid indexes."""
        files = ["/path/to/a.jpg", "/path/to/b.jpg", "/path/to/c.jpg"]
        fm = FileManager(files)

        paths = fm.get_paths([0, 2])
        assert paths == ["/path/to/a.jpg", "/path/to/c.jpg"]

    @pytest.mark.unit
    def test_get_paths_invalid_index_raises_error(self):
        """Test getting paths with invalid index raises ValueError."""
        fm = FileManager(["/path/to/file.jpg"])

        with pytest.raises(ValueError, match="File index 3 out of range"):
            fm.get_paths([0, 3])

    @pytest.mark.unit
    def test_format_context_empty(self):
        """Test format_context returns empty string when no files."""
        fm = FileManager([])
        assert fm.format_context() == ""

    @pytest.mark.unit
    def test_format_context_single_file(self):
        """Test format_context with single file."""
        fm = FileManager(["/path/to/photo.jpg"])

        result = fm.format_context()
        expected = "Files:\n- [0] /path/to/photo.jpg"
        assert result == expected

    @pytest.mark.unit
    def test_format_context_multiple_files(self):
        """Test format_context with multiple files."""
        files = [
            "/path/to/photo.jpg",
            "/path/to/document.pdf",
            "/path/to/data.csv",
        ]
        fm = FileManager(files)

        result = fm.format_context()
        expected = (
            "Files:\n"
            "- [0] /path/to/photo.jpg\n"
            "- [1] /path/to/document.pdf\n"
            "- [2] /path/to/data.csv"
        )
        assert result == expected

    @pytest.mark.unit
    def test_format_context_preserves_full_paths(self):
        """Test that full file paths are preserved."""
        fm = FileManager(["/Users/user/Documents/my file with spaces.pdf"])

        result = fm.format_context()
        assert "/Users/user/Documents/my file with spaces.pdf" in result
        assert "- [0]" in result
