"""CDP snapshot parser."""

from typing import Any, Dict, List, Optional, Callable, Tuple

from ..domnode import DomNode, Text, BoundingBox


def _get_string_resolver(strings: List[str]) -> Callable[[Any], str]:
    """Create a function to resolve string indices from the CDP strings array."""

    def resolve(index: Any) -> str:
        if isinstance(index, int) and 0 <= index < len(strings):
            return strings[index]
        return ""

    return resolve


def _parse_layout_data(
    layout_data: Dict[str, Any], get_string: Callable[[Any], str]
) -> Dict[int, Tuple[Optional[BoundingBox], Dict[str, str]]]:
    """
    Parse layout information from CDP snapshot.

    Important: CDP only includes layout data for nodes in the browser's render tree.
    Nodes that are not rendered (e.g., display:none, detached, etc.) will NOT be
    in this layout data.

    Returns a map from node index to (bounds, styles).
    """
    layout_node_indices = layout_data.get("nodeIndex", [])
    layout_bounds = layout_data.get("bounds", [])
    layout_styles = layout_data.get("styles", [])

    layout_map = {}
    requested_properties = ["display", "visibility", "opacity"]

    for i, node_idx in enumerate(layout_node_indices):
        # Parse bounding box
        bounds = None
        if i < len(layout_bounds):
            b = layout_bounds[i]
            if len(b) >= 4:
                bounds = BoundingBox(x=b[0], y=b[1], width=b[2], height=b[3])

        # Parse computed styles
        styles = {}
        if i < len(layout_styles):
            style_values = layout_styles[i]
            for j, value_idx in enumerate(style_values):
                if j < len(requested_properties):
                    prop_name = requested_properties[j]
                    prop_value = get_string(value_idx)
                    if prop_value:
                        styles[prop_name] = prop_value

        layout_map[node_idx] = (bounds, styles)

    return layout_map


def _create_element_nodes(
    nodes_data: Dict[str, Any],
    layout_map: Dict[int, Tuple[Optional[BoundingBox], Dict[str, str]]],
    get_string: Callable[[Any], str],
) -> List[Optional[DomNode]]:
    """
    Create DomNode objects for element nodes (node_type == 1).

    Returns a list where element nodes are at their CDP index and other types are None.
    """
    node_types = nodes_data.get("nodeType", [])
    node_names = nodes_data.get("nodeName", [])
    attributes_arrays = nodes_data.get("attributes", [])
    backend_node_ids = nodes_data.get("backendNodeId", [])

    num_nodes = len(node_types)
    nodes: List[Optional[DomNode]] = [None] * num_nodes

    for i in range(num_nodes):
        node_type = node_types[i] if i < len(node_types) else 0

        # Only process element nodes (type 1)
        if node_type != 1:
            continue

        # Parse attributes
        node_attrs = {}
        attributes = attributes_arrays[i] if i < len(attributes_arrays) else []
        for j in range(0, len(attributes), 2):
            if j + 1 < len(attributes):
                attr_name = get_string(attributes[j])
                attr_value = get_string(attributes[j + 1])
                if attr_name and attr_value:
                    node_attrs[attr_name] = attr_value

        # Get tag name
        node_name_idx = node_names[i] if i < len(node_names) else None
        tag_name = (
            get_string(node_name_idx).lower()
            if node_name_idx is not None
            else "unknown"
        )

        # Get layout info from CDP
        # Note: (None, {}) means CDP did not include this node in the render tree
        bounds, styles = layout_map.get(i, (None, {}))

        # Get backend node ID from CDP
        backend_node_id = backend_node_ids[i] if i < len(backend_node_ids) else None

        # Create node
        node = DomNode(
            tag=tag_name,
            attrib=node_attrs,
            styles=styles,
            bounds=bounds,
            backend_dom_node_id=backend_node_id,
            metadata={"cdp_index": i},
        )

        nodes[i] = node

    return nodes


def _add_text_nodes(
    nodes_data: Dict[str, Any],
    element_nodes: List[Optional[DomNode]],
    get_string: Callable[[Any], str],
) -> None:
    """Add text nodes (node_type == 3) as children to their parent elements."""
    node_types = nodes_data.get("nodeType", [])
    node_values = nodes_data.get("nodeValue", [])
    parent_indices = nodes_data.get("parentIndex", [])

    num_nodes = len(node_types)

    for i in range(num_nodes):
        node_type = node_types[i] if i < len(node_types) else 0

        # Only process text nodes (type 3)
        if node_type != 3:
            continue

        # Find parent element
        parent_idx = parent_indices[i] if i < len(parent_indices) else None
        if parent_idx is None or not (0 <= parent_idx < len(element_nodes)):
            continue

        parent_node = element_nodes[parent_idx]
        if parent_node is None:
            continue

        # Get text content
        node_value_idx = node_values[i] if i < len(node_values) else None
        text_content = get_string(node_value_idx) if node_value_idx is not None else ""

        # Add non-empty text as child
        if text_content.strip():
            parent_node.add_child(Text(text_content))


def _build_tree(
    nodes_data: Dict[str, Any], element_nodes: List[Optional[DomNode]]
) -> Optional[DomNode]:
    """
    Build the DOM tree by linking child nodes to parents.

    Returns the root node of the tree.
    """
    node_types = nodes_data.get("nodeType", [])
    parent_indices = nodes_data.get("parentIndex", [])

    num_nodes = len(node_types)
    root_node = None

    for i in range(num_nodes):
        current_node = element_nodes[i]
        if current_node is None:
            continue

        # Get parent index
        parent_idx = parent_indices[i] if i < len(parent_indices) else None

        if parent_idx is not None and parent_idx != -1:
            # Has parent - add as child
            if 0 <= parent_idx < len(element_nodes):
                parent_node = element_nodes[parent_idx]
                if parent_node is not None:
                    parent_node.add_child(current_node)
        else:
            # No parent - this is the root
            if root_node is None:
                root_node = current_node

    # Fallback: if no root found, use first non-None node
    if root_node is None:
        for node in element_nodes:
            if node is not None:
                root_node = node
                break

    return root_node


def parse_cdp(snapshot_data: Dict[str, Any]) -> DomNode:
    """
    Parse CDP snapshot into DomNode tree.
    """
    documents_data = snapshot_data.get("documents", [])
    strings = snapshot_data.get("strings", [])

    # Handle empty snapshot
    if not documents_data:
        return DomNode(tag="html", metadata={"cdp_index": 0})

    # Get document data
    document_data = documents_data[0]
    nodes_data = document_data.get("nodes", {})
    layout_data = document_data.get("layout", {})

    # Create string resolver
    get_string = _get_string_resolver(strings)

    # Parse layout information
    layout_map = _parse_layout_data(layout_data, get_string)

    # Create element nodes
    element_nodes = _create_element_nodes(nodes_data, layout_map, get_string)

    # Add text nodes as children
    _add_text_nodes(nodes_data, element_nodes, get_string)

    # Build tree structure
    root_node = _build_tree(nodes_data, element_nodes)

    # Final fallback
    if root_node is None:
        root_node = DomNode(tag="html", metadata={"cdp_index": 0})

    return root_node
