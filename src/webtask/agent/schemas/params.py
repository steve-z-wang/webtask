"""Parameter schemas for agent actions - base class only.

Individual parameter classes are now defined in their respective tool files:
- ClickParams: tools/browser/click.py
- FillParams: tools/browser/fill.py
- TypeParams: tools/browser/type.py
- NavigateParams: tools/browser/navigate.py
- UploadParams: tools/browser/upload.py
- MarkCompleteParams: tools/control/mark_complete.py
"""

from pydantic import BaseModel
from typing import Dict, Any


class ToolParams(BaseModel):
    """Base class for tool parameters using Pydantic for validation."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """Generate JSON schema for LLM tool calling."""
        return cls.model_json_schema()
