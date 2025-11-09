"""Content types for LLM input."""

from enum import Enum
from typing import Union, List
from pydantic import BaseModel


class ImageType(str, Enum):
    """Supported image MIME types."""

    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    GIF = "image/gif"


class Text(BaseModel):
    """Text content part."""

    text: str


class Image(BaseModel):
    """Image content part (base64-encoded)."""

    data: str  # base64-encoded image
    mime_type: ImageType = ImageType.PNG  # Image format


# Union type for content parts
Content = Union[Text, Image]

# Type alias for ordered list of content
ContentList = List[Content]
