"""Image class for handling screenshots and visual data."""

import base64


class Image:
    """Represents an image with convenient conversion methods."""

    def __init__(self, data: bytes, format: str = "png"):
        """Initialize Image with raw bytes.

        Args:
            data: Raw image bytes
            format: Image format (default: "png")
        """
        self._data = data
        self._format = format

    def to_base64(self) -> str:
        """Convert image to base64 string for LLM APIs.

        Returns:
            Base64-encoded string
        """
        return base64.b64encode(self._data).decode("utf-8")

    def to_data_url(self) -> str:
        """Convert image to data URL for embedding in HTML or sending to APIs.

        Returns:
            Data URL string (e.g., "data:image/png;base64,...")
        """
        b64 = self.to_base64()
        return f"data:image/{self._format};base64,{b64}"

    def save(self, path: str) -> None:
        """Save image to file.

        Args:
            path: File path to save to
        """
        with open(path, "wb") as f:
            f.write(self._data)

    def to_bytes(self) -> bytes:
        """Get raw image bytes.

        Returns:
            Raw bytes
        """
        return self._data

    @property
    def format(self) -> str:
        """Get image format.

        Returns:
            Format string (e.g., "png")
        """
        return self._format

    @property
    def size(self) -> int:
        """Get size in bytes.

        Returns:
            Size in bytes
        """
        return len(self._data)

    def __repr__(self) -> str:
        return f"Image(format={self._format}, size={self.size} bytes)"
