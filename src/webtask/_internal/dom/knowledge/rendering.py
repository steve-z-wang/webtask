"""Knowledge: Determine if elements are rendered."""

from typing import Union
from ..domnode import DomNode, Text


def is_not_rendered(node: Union[DomNode, Text]) -> bool:
    """Check if node is not rendered (no layout data from CDP).

    Text nodes are always considered rendered (they don't have layout data).
    """
    # Text nodes don't have rendering info - consider them rendered
    if isinstance(node, Text):
        return False

    # DomNode rendering check
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None
    return not has_styles and not has_bounds


def should_keep_when_not_rendered(node: Union[DomNode, Text]) -> bool:
    """Check if non-rendered node should be kept (file/hidden inputs).

    Only applies to specific DomNode types like file inputs.
    """
    # Only applies to DomNodes
    if isinstance(node, Text):
        return False

    if node.tag == "input":
        input_type = node.attrib.get("type", "").lower()
        return input_type in ("file", "hidden")
    return False
