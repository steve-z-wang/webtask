"""Base ToolParams class for tool parameters."""

from typing import Dict, Any
from pydantic import BaseModel


class ToolParams(BaseModel):
    """Base class for tool parameters using Pydantic for validation."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """Generate JSON schema for LLM tool calling."""
        return cls.model_json_schema()
