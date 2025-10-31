"""DomContextBuilder - builds LLM context from DOM."""

from typing import Dict, Optional
from ..browser import Page
from ..dom.domnode import DomNode, Text
from .dom_filter_config import DomFilterConfig
from .filters import apply_visibility_filters, apply_semantic_filters


class DomContextBuilder:
    """Static builder for creating LLM context from DOM."""

    @staticmethod
    async def build_context(
        page: Page,
        dom_filter_config: Optional[DomFilterConfig] = None,
    ) -> tuple[Optional[str], Dict[str, DomNode]]:
        """Build context string and element map from page.

        Returns: (context_string, element_map)
                 context_string is None if all elements filtered out
                 element_map maps element_id -> original unfiltered node
        """

        dom_filter_config = dom_filter_config or DomFilterConfig()

        snapshot = await page.get_snapshot()
        root = snapshot.root

        # Add reference to original nodes before filtering
        root = DomContextBuilder._add_node_reference(root)

        root = apply_visibility_filters(root, dom_filter_config)
        root = apply_semantic_filters(root, dom_filter_config)

        if root is None:
            return None, {}

        element_map = DomContextBuilder._assign_element_ids(root, dom_filter_config)
        context_str = DomContextBuilder._serialize_context(root)

        return context_str, element_map

    @staticmethod
    def _assign_element_ids(root: DomNode, dom_filter_config: DomFilterConfig) -> Dict[str, DomNode]:
        """Assign element IDs only to interactive nodes.

        Non-interactive nodes still appear in context but without IDs.
        Only interactive elements get IDs and go into element_map.

        An element is considered interactive if:
        - Its tag is in interactive_tags (e.g., button, input, a)
        - Its role attribute is in interactive_roles (e.g., role="button")
        """
        element_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if isinstance(node, DomNode):
                # Check if element is interactive by tag or role
                is_interactive_tag = node.tag in dom_filter_config.interactive_tags
                element_role = node.attrib.get('role')
                is_interactive_role = element_role in dom_filter_config.interactive_roles if element_role else False

                if is_interactive_tag or is_interactive_role:
                    tag = node.tag
                    count = tag_counters.get(tag, 0)
                    element_id = f"{tag}-{count}"

                    node.metadata['element_id'] = element_id

                    # Map to original unfiltered node for correct XPath computation
                    original_node = node.metadata.get('original_node', node)
                    element_map[element_id] = original_node

                    tag_counters[tag] = count + 1

        return element_map

    @staticmethod
    def _serialize_context(root: DomNode) -> str:
        """Serialize DomNode tree to markdown format."""
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

        traverse(root, 0)
        return "\n".join(lines)

    @staticmethod
    def _add_node_reference(root: DomNode) -> DomNode:
        """Add original_node reference to metadata before filtering."""
        for node in root.traverse():
            if isinstance(node, DomNode):
                node.metadata['original_node'] = node

        return root
