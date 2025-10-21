"""Serialization for DomNode trees to markdown format."""

from ..domnode import DomNode, Text


def serialize_to_markdown(node: DomNode) -> str:
    """
    Serialize DomNode tree to markdown bullet list format.

    Args:
        node: Root node of tree

    Returns:
        Markdown string with indented bullet list

    Example:
        - body
          - div (role="navigation")
            - a
              - "About"
    """
    lines = []

    def traverse(n: DomNode, depth: int = 0):
        """Recursively traverse and build markdown."""
        indent = "  " * depth

        # Get element ID or fallback to tag
        element_id = n.metadata.get("element_id", n.tag)

        # Format attributes
        attr_parts = []
        if n.attrib:
            attr_strs = [f'{k}="{v}"' for k, v in n.attrib.items()]
            attr_parts.append(f'({" ".join(attr_strs)})')

        # Build line
        markdown = f"{element_id}"
        if attr_parts:
            markdown += f" {' '.join(attr_parts)}"

        lines.append(f"{indent}- {markdown}")

        # Process children
        for child in n.children:
            if isinstance(child, DomNode):
                traverse(child, depth + 1)
            elif isinstance(child, Text):
                # Add text nodes as quoted strings
                text_indent = "  " * (depth + 1)
                lines.append(f'{text_indent}- "{child.content}"')

    traverse(node, 0)
    return "\n".join(lines)
