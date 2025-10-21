"""Filter presentational role attributes (role='none' or role='presentation')."""

from ...domnode import DomNode, Text


def filter_presentational_roles(node: DomNode) -> DomNode:
    """
    Filter presentational role attributes.

    Removes role='none' or role='presentation' attributes from elements.
    These roles explicitly declare that an element has no semantic meaning,
    so we remove the confusing attribute while preserving the element structure.

    Args:
        node: DomNode to process

    Returns:
        New DomNode with presentational roles filtered out

    Example:
        >>> node = DomNode(tag='ul', attrib={'role': 'none'})
        >>> filtered = filter_presentational_roles(node)
        >>> filtered.attrib
        {}
    """
    # Create new node with copied data (since we might modify attributes)
    new_node = node.deepcopy()

    # Check if this node has presentational role and remove it
    role = new_node.attrib.get('role', '').lower()
    if role in ('none', 'presentation'):
        # Remove the role attribute
        del new_node.attrib['role']

    # Recursively process children
    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_presentational_roles(child)
            new_node.add_child(filtered_child)

    return new_node
