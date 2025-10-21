"""Base ToolParams class for tool parameters."""

from typing import Dict, Any
from pydantic import BaseModel


class ToolParams(BaseModel):
    """
    Base class for tool parameters.

    Uses Pydantic for automatic validation and schema generation.
    Subclasses define typed parameters with Field() for descriptions.
    """

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """
        Generate JSON schema for LLM tool calling.

        Returns:
            JSON schema dict with parameter definitions

        Example:
            >>> NavigateParams.schema()
            {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"}
                },
                "required": ["url"]
            }
        """
        return cls.model_json_schema()
