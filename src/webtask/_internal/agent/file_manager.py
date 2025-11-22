"""FileManager - manages files for upload tasks."""

from typing import List, Optional


class FileManager:
    """Manages files for upload tasks."""

    def __init__(self, files: Optional[List[str]] = None):
        """Initialize with optional list of file paths."""
        self._files = files or []

    def is_empty(self) -> bool:
        """Check if no files are available."""
        return len(self._files) == 0

    def get_path(self, index: int) -> str:
        """Get file path by index.

        Args:
            index: 0-based file index

        Returns:
            File path

        Raises:
            ValueError: If index is out of range
        """
        if index < 0 or index >= len(self._files):
            raise ValueError(
                f"File index {index} out of range (0-{len(self._files) - 1})"
            )
        return self._files[index]

    def get_paths(self, indexes: List[int]) -> List[str]:
        """Get multiple file paths by indexes.

        Args:
            indexes: List of 0-based file indexes

        Returns:
            List of file paths

        Raises:
            ValueError: If any index is out of range
        """
        return [self.get_path(i) for i in indexes]

    def format_context(self) -> str:
        """Format files for LLM context.

        Returns:
            Formatted string like:
            Files:
            - [0] /path/to/file1.jpg
            - [1] /path/to/file2.pdf
        """
        if self.is_empty():
            return ""
        lines = ["Files:"]
        for idx, path in enumerate(self._files):
            lines.append(f"- [{idx}] {path}")
        return "\n".join(lines)
