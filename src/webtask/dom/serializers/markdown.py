"""Markdown serialization."""

from ..domnode import DomNode, Text


def serialize_to_markdown(node: DomNode) -> str:
    """Serialize DomNode tree to markdown."""
    lines = []

    def traverse(n: DomNode, depth: int = 0):
        indent = "  " * depth

        element_id = n.metadata.get("element_id", n.tag)

        attr_parts = []
        if n.attrib:
            attr_strs = [f'{k}="{v}"' for k, v in n.attrib.items()]
            attr_parts.append(f'({" ".join(attr_strs)})')

        markdown = f"{element_id}"
        if attr_parts:
            markdown += f" {' '.join(attr_parts)}"

        lines.append(f"{indent}- {markdown}")

        for child in n.children:
            if isinstance(child, DomNode):
                traverse(child, depth + 1)
            elif isinstance(child, Text):
                text_indent = "  " * (depth + 1)
                lines.append(f'{text_indent}- "{child.content}"')

    traverse(node, 0)
    return "\n".join(lines)
