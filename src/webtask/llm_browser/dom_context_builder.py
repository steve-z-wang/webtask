"""DomContextBuilder - builds LLM context from DOM."""

from typing import Dict, Optional
from ..browser import Page
from ..dom.domnode import DomNode, Text
from .dom_filter_config import DomFilterConfig
from .filters.visibility import filter_not_rendered
from .filters.semantic import (
    filter_attributes,
    filter_presentational_roles,
    filter_empty,
    collapse_single_child_wrappers,
)


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

        # Apply visibility filters
        if dom_filter_config.filter_not_rendered and root is not None:
            root = filter_not_rendered(root)

        if root is None:
            return None, {}

        # Apply semantic filters
        if dom_filter_config.filter_attributes and root is not None:
            root = filter_attributes(root, dom_filter_config.kept_attributes)

        if dom_filter_config.filter_presentational_roles and root is not None:
            root = filter_presentational_roles(root)

        if dom_filter_config.filter_empty and root is not None:
            root = filter_empty(root)

        if dom_filter_config.collapse_wrappers and root is not None:
            root = collapse_single_child_wrappers(root)

        if root is None:
            return None, {}

        element_map = DomContextBuilder._assign_element_ids(root, dom_filter_config)
        context_str = DomContextBuilder._serialize_context(root)

        return context_str, element_map

    @staticmethod
    def _assign_element_ids(
        root: DomNode, dom_filter_config: DomFilterConfig
    ) -> Dict[str, DomNode]:
        """Assign element IDs to ALL nodes.

        All elements get IDs and appear in element_map, allowing LLM to reference any element.
        For bounding boxes, caller should filter to only interactive elements.

        Returns:
            element_map: Maps element_id -> original unfiltered node
        """
        element_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if isinstance(node, DomNode):
                tag = node.tag
                count = tag_counters.get(tag, 0)
                element_id = f"{tag}-{count}"

                node.metadata["element_id"] = element_id

                # Map to original unfiltered node for correct XPath computation
                original_node = node.metadata.get("original_node", node)
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
                node.metadata["original_node"] = node

        return root
