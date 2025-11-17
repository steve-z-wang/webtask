"""CDP accessibility tree parser.

Parses raw Chrome DevTools Protocol accessibility tree data into AXNode IR.
"""

from typing import Dict, Any, Optional
from ..axnode import AXNode, AXValue, AXProperty


def _parse_ax_value(value_data: Optional[Dict[str, Any]]) -> Optional[AXValue]:
    """Parse an AXValue from CDP data."""
    if not value_data:
        return None

    return AXValue(
        type=value_data.get("type", "string"),
        value=value_data.get("value"),
        sources=value_data.get("sources", []),
    )


def _parse_ax_property(prop_data: Dict[str, Any]) -> AXProperty:
    """Parse an AXProperty from CDP data."""
    return AXProperty(
        name=prop_data.get("name", ""),
        value=_parse_ax_value(prop_data.get("value")) or AXValue(type="string"),
    )


def parse_cdp_accessibility(cdp_data: Dict[str, Any]) -> AXNode:
    """
    Parse CDP accessibility tree into AXNode tree.
    """
    nodes_data = cdp_data.get("nodes", [])

    if not nodes_data:
        # Return empty root node
        return AXNode(node_id="root", role=AXValue(type="role", value="RootWebArea"))

    # First pass: Create all AXNode objects (temporarily store CDP IDs)
    nodes_map: Dict[str, AXNode] = {}
    node_data_map: Dict[str, Dict[str, Any]] = {}

    for node_data in nodes_data:
        # Parse role, defaulting to "unknown" if missing
        role = _parse_ax_value(node_data.get("role"))
        if role is None or not role.value:
            role = AXValue(type="role", value="unknown")

        node = AXNode(
            node_id=node_data.get("nodeId", ""),
            backend_dom_node_id=node_data.get("backendDOMNodeId"),
            ignored=node_data.get("ignored", False),
            ignored_reasons=node_data.get("ignoredReasons", []),
            role=role,
            chrome_role=_parse_ax_value(node_data.get("chromeRole")),
            name=_parse_ax_value(node_data.get("name")),
            description=_parse_ax_value(node_data.get("description")),
            value=_parse_ax_value(node_data.get("value")),
            properties=[_parse_ax_property(p) for p in node_data.get("properties", [])],
            frame_id=node_data.get("frameId"),
        )

        nodes_map[node.node_id] = node
        node_data_map[node.node_id] = node_data

    # Second pass: Build parent-child relationships using CDP IDs
    root_node = None

    for node_id, node in nodes_map.items():
        node_data = node_data_map[node_id]

        # Link children
        child_ids = node_data.get("childIds", [])
        for child_id in child_ids:
            if child_id in nodes_map:
                child = nodes_map[child_id]
                node.children.append(child)
                child.parent = node  # Set parent reference

        # Find root (node with no parent or parent not in tree)
        parent_id = node_data.get("parentId")
        if parent_id is None or parent_id not in nodes_map:
            if root_node is None:
                root_node = node

    # Fallback: if no root found, use first node
    if root_node is None and nodes_map:
        root_node = list(nodes_map.values())[0]

    # Final fallback
    if root_node is None:
        root_node = AXNode(
            node_id="root", role=AXValue(type="role", value="RootWebArea")
        )

    return root_node
