"""HTML string parser.

Parses HTML strings into DomNode trees.
Supports optional attributes for browser data (backend_node_id, bounding boxes).
"""

from typing import Optional

from lxml import etree
from lxml import html as lxml_html

from ..domnode import DomNode, Text, BoundingBox


def parse_html(html_string: str) -> DomNode:
    """
    Parse HTML string into DomNode tree.

    Supports optional attributes for browser data:
    - backend_node_id: CDP backend node ID
    - bounding_box_rect: Bounding box as "x,y,width,height"
    - style: Inline styles (computed styles need CDP)

    Args:
        html_string: HTML string to parse

    Returns:
        Root DomNode of the parsed tree

    Example:
        >>> html = '<div class="container"><button>Click</button></div>'
        >>> root = parse_html(html)
        >>> root.tag
        'div'
        >>> root.children[0].tag
        'button'
    """
    # Handle empty HTML
    if not html_string or not html_string.strip():
        return DomNode(tag="html")

    # Parse HTML with lxml
    try:
        # Try parsing as XML first (preserves custom tags)
        parser = etree.XMLParser(recover=True, remove_blank_text=False)
        tree = etree.fromstring(html_string.encode("utf-8"), parser=parser)
    except:
        # Fallback to HTML parser
        tree = lxml_html.fromstring(html_string)

    # Convert lxml tree to DomNode tree
    root_node = _convert_lxml_to_node(tree)

    return root_node


def _parse_bounding_box(bbox_str: str) -> Optional[BoundingBox]:
    """
    Parse bounding_box_rect attribute.

    Format: "x,y,width,height" (e.g., "10.5,20,100,50")

    Returns:
        BoundingBox or None if invalid
    """
    if not bbox_str:
        return None

    try:
        parts = bbox_str.split(",")
        if len(parts) >= 4:
            x, y, width, height = parts[:4]
            return BoundingBox(x=float(x), y=float(y), width=float(width), height=float(height))
    except (ValueError, AttributeError):
        pass

    return None


def _parse_inline_styles(style_str: str) -> dict:
    """
    Parse inline style attribute into dict.

    Format: "display: block; color: red"

    Returns:
        Dictionary of style properties
    """
    if not style_str:
        return {}

    styles = {}
    for pair in style_str.split(";"):
        if ":" in pair:
            key, value = pair.split(":", 1)
            styles[key.strip()] = value.strip()

    return styles


def _convert_lxml_to_node(lxml_node) -> DomNode:
    """
    Recursively convert lxml Element to DomNode.

    Args:
        lxml_node: lxml Element

    Returns:
        DomNode with children
    """
    # Get tag name
    tag_name = lxml_node.tag if isinstance(lxml_node.tag, str) else str(lxml_node.tag)
    tag_name = tag_name.lower()

    # Handle special <text> elements (custom tags used in some datasets)
    if tag_name == "text":
        # Extract text content
        text_content = (lxml_node.text or "").strip()
        if text_content:
            # Return a text node wrapped in a span for compatibility
            node = DomNode(tag="span")
            node.add_child(Text(text_content))
            return node
        # Empty text element, return empty span
        return DomNode(tag="span")

    # Extract attributes
    attributes = dict(lxml_node.attrib)

    # Parse metadata
    metadata = {}
    if "backend_node_id" in attributes:
        try:
            metadata["backend_node_id"] = int(attributes["backend_node_id"])
        except (ValueError, TypeError):
            pass

    # Parse bounding box if present
    bbox_str = attributes.get("bounding_box_rect", "")
    bounds = _parse_bounding_box(bbox_str)

    # Parse inline styles
    style_str = attributes.get("style", "")
    styles = _parse_inline_styles(style_str)

    # Remove special attributes from attrib (keep only regular HTML attributes)
    attrib = {k: v for k, v in attributes.items() if k not in {"backend_node_id", "bounding_box_rect"}}

    # Create DomNode
    node = DomNode(tag=tag_name, attrib=attrib, styles=styles, bounds=bounds, metadata=metadata)

    # Process text content before first child
    if lxml_node.text:
        text_content = lxml_node.text.strip()
        if text_content:
            node.add_child(Text(text_content))

    # Process children
    for child in lxml_node:
        child_node = _convert_lxml_to_node(child)
        if child_node:
            node.add_child(child_node)

        # Process tail text (text after closing tag)
        if child.tail:
            tail_content = child.tail.strip()
            if tail_content:
                node.add_child(Text(tail_content))

    return node
