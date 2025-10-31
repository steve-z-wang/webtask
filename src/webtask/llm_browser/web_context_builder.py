"""WebContextBuilder - builds LLM context from page DOM."""

from typing import Dict, Optional
from ..browser import Page
from ..dom.domnode import DomNode
from ..dom.dom_context_config import DomContextConfig
from ..dom.filters import apply_visibility_filters, apply_semantic_filters
from ..dom.utils import add_node_reference


class WebContextBuilder:
    """Static builder for creating LLM context from web pages."""

    @staticmethod
    async def build_context(
        page: Page,
        dom_context_config: Optional[DomContextConfig] = None,
    ) -> tuple[str, Dict[str, DomNode]]:
        """Build context string and element map from page.

        Returns: (context_string, element_map)
        """
        
        dom_context_config = dom_context_config or DomContextConfig() 
        
        snapshot = await page.get_snapshot()
        root = snapshot.root

        root = add_node_reference(root)
        root = apply_visibility_filters(root, dom_context_config)
        root = apply_semantic_filters(root, dom_context_config)

        if root is None:
            context_str = WebContextBuilder._build_error_context(snapshot.url)
            return context_str, {}

        element_map = WebContextBuilder._assign_element_ids(root)
        context_str = WebContextBuilder._serialize_context(root, snapshot.url)

        return context_str, element_map

    @staticmethod
    def _build_error_context(url: str) -> str:
        lines = ["Page:"]

        if not url or url == "about:blank":
            lines.append("  URL: (no page loaded)")
            lines.append("")
            lines.append("ERROR: No URL loaded yet.")
            lines.append("Please use the navigate tool to navigate to a URL.")
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
        from ..dom.serializers import serialize_to_markdown

        lines = ["Page:"]

        if url:
            lines.append(f"  URL: {url}")
            lines.append("")

        lines.append(serialize_to_markdown(root))

        return "\n".join(lines)
