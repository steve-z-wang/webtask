"""Knowledge: Determine if elements are rendered."""

from ...dom.domnode import DomNode


def is_not_rendered(node: DomNode) -> bool:
    """Check if element is not rendered (no layout data from CDP)."""
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None
    return not has_styles and not has_bounds


def should_keep_when_not_rendered(node: DomNode) -> bool:
    """Check if non-rendered element should be kept (file/hidden inputs)."""
    if node.tag == "input":
        input_type = node.attrib.get("type", "").lower()
        return input_type in ("file", "hidden")
    return False
