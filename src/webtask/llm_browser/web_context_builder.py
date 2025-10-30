"""WebContextBuilder - builds LLM context from page DOM."""

from typing import Dict
from ..browser import Page
from ..dom.domnode import DomNode
from ..dom.dom_context_config import DomContextConfig
from ..dom.filters import apply_visibility_filters, apply_semantic_filters
from ..dom.utils import add_node_reference


class WebContextBuilder:
    """
    Static builder for creating LLM context from web pages.

    Pure functional approach - no state, just input → output.
    """

    @staticmethod
    async def build_context(
        page: Page,
        dom_context_config: DomContextConfig
    ) -> tuple[str, Dict[str, DomNode]]:
        """
        Build context string and element map from page.

        Pure function with no side effects.

        Args:
            page: Page instance to build context from
            dom_context_config: DOM filtering configuration

        Returns:
            Tuple of (context_string, element_map)
            - context_string: Formatted page context with element IDs
            - element_map: Mapping of element_id -> DomNode

        Example:
            >>> config = DomContextConfig()
            >>> context_str, element_map = await WebContextBuilder.build_context(page, config)
            >>> print(context_str)
            Page:
              URL: https://example.com

            # a-0
            [More information...](https://www.iana.org/domains/example)

            >>> print(element_map.keys())
            dict_keys(['a-0'])
        """
        # Get raw snapshot from page
        snapshot = await page.get_snapshot()
        root = snapshot.root

        # Add node references (before filtering)
        root = add_node_reference(root)

        # Apply filters with config
        root = apply_visibility_filters(root, dom_context_config)
        root = apply_semantic_filters(root, dom_context_config)

        # Handle case where filtering removes everything
        if root is None:
            context_str = WebContextBuilder._build_error_context(snapshot.url)
            return context_str, {}

        # Assign element IDs and build mapping
        element_map = WebContextBuilder._assign_element_ids(root)

        # Serialize to markdown
        context_str = WebContextBuilder._serialize_context(root, snapshot.url)

        return context_str, element_map

    @staticmethod
    def _build_error_context(url: str) -> str:
        """
        Build error context when no elements are found.

        Args:
            url: Page URL (or None/empty if not loaded)

        Returns:
            Error context string
        """
        lines = ["Page:"]

        # Case 1: Page opened but no URL (not navigated)
        if not url or url == "about:blank":
            lines.append("  URL: (no page loaded)")
            lines.append("")
            lines.append("ERROR: No URL loaded yet.")
            lines.append("Please use the navigate tool to navigate to a URL.")
        # Case 2: Navigated to URL but no elements
        else:
            lines.append(f"  URL: {url}")
            lines.append("")
            lines.append("ERROR: No visible interactive elements found on this page.")
            lines.append("")
            lines.append("Possible causes:")
            lines.append("- The page is still loading")
            lines.append("- The page has no interactive elements")
            lines.append("- All elements were filtered out")

        return "\n".join(lines)

    @staticmethod
    def _assign_element_ids(root: DomNode) -> Dict[str, DomNode]:
        """
        Assign element IDs to all nodes and build mapping.

        Modifies nodes in-place by adding 'element_id' to metadata.

        Args:
            root: Root DOM node

        Returns:
            Dictionary mapping element_id -> DomNode
        """
        element_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if isinstance(node, DomNode):
                tag = node.tag
                count = tag_counters.get(tag, 0)
                element_id = f"{tag}-{count}"

                node.metadata['element_id'] = element_id
                element_map[element_id] = node

                tag_counters[tag] = count + 1

        return element_map

    @staticmethod
    def _serialize_context(root: DomNode, url: str) -> str:
        """
        Serialize DOM to markdown context string.

        Args:
            root: Root DOM node with element IDs assigned
            url: Page URL

        Returns:
            Formatted context string
        """
        from ..dom.serializers import serialize_to_markdown

        lines = ["Page:"]

        if url:
            lines.append(f"  URL: {url}")
            lines.append("")

        lines.append(serialize_to_markdown(root))

        return "\n".join(lines)
