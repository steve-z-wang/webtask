"""Parameter schemas for agent actions."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


# Base class for all tool parameters
class ToolParams(BaseModel):
    """Base class for tool parameters using Pydantic for validation."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """Generate JSON schema for LLM tool calling."""
        return cls.model_json_schema()


# Parameter schemas for each tool type
class ClickParams(ToolParams):
    """Parameters for click action."""

    element_id: str = Field(description="ID of the element to click")


class FillParams(ToolParams):
    """Parameters for fill action."""

    element_id: str = Field(description="ID of the element to fill")
    value: str = Field(description="Value to fill into the element")


class NavigateParams(ToolParams):
    """Parameters for navigate action."""

    url: str = Field(description="URL to navigate to")


class TypeParams(ToolParams):
    """Parameters for type action."""

    element_id: str = Field(description="ID of the element to type into")
    text: str = Field(description="Text to type into the element")


class UploadParams(ToolParams):
    """Parameters for upload action."""

    element_id: str = Field(
        description="Element ID of the file input (e.g., 'input-5')"
    )
    resource_names: List[str] = Field(
        description="List of resource names to upload (e.g., ['photo1', 'photo2'])"
    )
