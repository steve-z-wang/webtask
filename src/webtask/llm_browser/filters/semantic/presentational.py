"""Filter presentational role attributes."""

from ....dom.domnode import DomNode, Text


def filter_presentational_roles(node: DomNode) -> DomNode:
    """Remove presentational role attributes."""
    new_node = node.deepcopy()

    role = new_node.attrib.get("role", "").lower()
    if role in ("none", "presentation"):
        del new_node.attrib["role"]

    for child in node.children:
        if isinstance(child, Text):
            new_node.add_child(Text(child.content))
        elif isinstance(child, DomNode):
            filtered_child = filter_presentational_roles(child)
            new_node.add_child(filtered_child)

    return new_node
