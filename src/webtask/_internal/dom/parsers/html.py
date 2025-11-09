"""HTML parser."""

from typing import Optional

from lxml import etree
from lxml import html as lxml_html

from ..domnode import DomNode, Text, BoundingBox


def parse_html(html_string: str) -> DomNode:
    """Parse HTML into DomNode tree."""
    if not html_string or not html_string.strip():
        return DomNode(tag="html")

    try:
        parser = etree.XMLParser(recover=True, remove_blank_text=False)
        tree = etree.fromstring(html_string.encode("utf-8"), parser=parser)
    except Exception:
        tree = lxml_html.fromstring(html_string)

    root_node = _convert_lxml_to_node(tree)

    return root_node


def _parse_bounding_box(bbox_str: str) -> Optional[BoundingBox]:
    if not bbox_str:
        return None

    try:
        parts = bbox_str.split(",")
        if len(parts) >= 4:
            x, y, width, height = parts[:4]
            return BoundingBox(
                x=float(x), y=float(y), width=float(width), height=float(height)
            )
    except (ValueError, AttributeError):
        pass

    return None


def _parse_inline_styles(style_str: str) -> dict:
    if not style_str:
        return {}

    styles = {}
    for pair in style_str.split(";"):
        if ":" in pair:
            key, value = pair.split(":", 1)
            styles[key.strip()] = value.strip()

    return styles


def _convert_lxml_to_node(lxml_node) -> DomNode:
    tag_name = lxml_node.tag if isinstance(lxml_node.tag, str) else str(lxml_node.tag)
    tag_name = tag_name.lower()

    if tag_name == "text":
        text_content = (lxml_node.text or "").strip()
        if text_content:
            node = DomNode(tag="span")
            node.add_child(Text(text_content))
            return node
        return DomNode(tag="span")

    attributes = dict(lxml_node.attrib)

    metadata = {}
    if "backend_node_id" in attributes:
        try:
            metadata["backend_node_id"] = int(attributes["backend_node_id"])
        except (ValueError, TypeError):
            pass

    bbox_str = attributes.get("bounding_box_rect", "")
    bounds = _parse_bounding_box(bbox_str)

    style_str = attributes.get("style", "")
    styles = _parse_inline_styles(style_str)

    attrib = {
        k: v
        for k, v in attributes.items()
        if k not in {"backend_node_id", "bounding_box_rect"}
    }

    node = DomNode(
        tag=tag_name, attrib=attrib, styles=styles, bounds=bounds, metadata=metadata
    )

    if lxml_node.text:
        text_content = lxml_node.text.strip()
        if text_content:
            node.add_child(Text(text_content))

    for child in lxml_node:
        child_node = _convert_lxml_to_node(child)
        if child_node:
            node.add_child(child_node)

        if child.tail:
            tail_content = child.tail.strip()
            if tail_content:
                node.add_child(Text(tail_content))

    return node
