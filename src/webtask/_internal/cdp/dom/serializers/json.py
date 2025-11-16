"""Serialize DomNode tree to JSON with complete data."""

from typing import Any, Dict, Union
from ..domnode import DomNode, Text


def serialize_to_json(node: Union[DomNode, Text]) -> Dict[str, Any]:
    """Serialize DomNode tree to JSON format with all data.

    Includes:
    - tag name
    - attributes (all key-value pairs)
    - styles (computed CSS properties from CDP)
    - bounds (bounding box: x, y, width, height)
    - metadata (extra data like element_id, original_node reference)
    - children (recursively serialized)
    """
    if isinstance(node, Text):
        return {"type": "text", "content": node.content}

    # Serialize bounding box if present
    bounds_dict = None
    if node.bounds:
        bounds_dict = {
            "x": node.bounds.x,
            "y": node.bounds.y,
            "width": node.bounds.width,
            "height": node.bounds.height,
        }

    # Filter metadata to avoid circular references
    # Skip 'original_node' as it causes infinite recursion
    filtered_metadata = {k: v for k, v in node.metadata.items() if k != "original_node"}

    # Recursively serialize children
    children_list = []
    for child in node.children:
        children_list.append(serialize_to_json(child))

    return {
        "type": "element",
        "tag": node.tag,
        "attributes": dict(node.attrib),  # All HTML attributes
        "styles": dict(node.styles),  # Computed styles from CDP
        "bounds": bounds_dict,  # Bounding box or None
        "metadata": filtered_metadata,  # Extra data (element_id, etc)
        "children": children_list,
    }


def serialize_tree_to_json_string(node: Union[DomNode, Text], indent: int = 2) -> str:
    """Serialize DomNode tree to formatted JSON string."""
    import json

    data = serialize_to_json(node)
    return json.dumps(data, indent=indent, ensure_ascii=False)
