"""LLM response schemas - all Pydantic models for structured LLM outputs."""

from .params import ToolParams
from ..tools.browser.click import ClickParams
from ..tools.browser.fill import FillParams
from ..tools.browser.navigate import NavigateParams
from ..tools.browser.type import TypeParams
from ..tools.browser.upload import UploadParams
from ..tools.control.mark_complete import MarkCompleteParams
from .proposal import Action, RoleType, Proposal
from .selector import SelectorResponse

__all__ = [
    # Base class
    "ToolParams",
    # Action schema
    "Action",
    # Parameter types
    "ClickParams",
    "FillParams",
    "NavigateParams",
    "TypeParams",
    "UploadParams",
    "MarkCompleteParams",
    # Role schemas
    "RoleType",
    "Proposal",
    # Response models
    "SelectorResponse",
]
