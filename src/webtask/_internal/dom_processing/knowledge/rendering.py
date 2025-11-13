
from webtask._internal.dom.domnode import DomNode


def is_not_rendered(node: DomNode) -> bool:
    has_styles = bool(node.styles)
    has_bounds = node.bounds is not None
    return not has_styles and not has_bounds


def should_keep_when_not_rendered(node: DomNode) -> bool:
    if node.tag == "input":
        input_type = node.attrib.get("type", "").lower()
        return input_type in ("file", "hidden")
    return False
