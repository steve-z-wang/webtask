"""LLMDomContext - builds LLM context with role_id/tag_id → DomNode lookup."""

from typing import Dict, Optional, TYPE_CHECKING
from ..dom import DomNode
from ..accessibility import AXNode
from ..accessibility.filters import (
    filter_ignored_nodes,
    filter_duplicate_text,
    filter_non_semantic_role,
)

if TYPE_CHECKING:
    from ...browser.page import Page


class LLMDomContext:
    """Builds LLM context from DOM and accessibility trees."""

    def __init__(
        self, dom_root: DomNode, ax_root: AXNode, include_element_ids: bool = True
    ):
        self.dom_root = dom_root
        self.ax_root = ax_root
        self.include_element_ids = include_element_ids
        self._context_str: Optional[str] = None
        self._element_map: Optional[Dict[str, DomNode]] = None

    @classmethod
    async def from_page(
        cls, page: "Page", include_element_ids: bool = True
    ) -> "LLMDomContext":
        """Create LLMDomContext from page."""
        dom_root = DomNode.from_cdp(await page.get_cdp_dom_snapshot())
        ax_root = AXNode.from_cdp(await page.get_cdp_accessibility_tree())
        return cls(
            dom_root=dom_root,
            ax_root=ax_root,
            include_element_ids=include_element_ids,
        )

    def get_context(self, mode: str = "accessibility") -> str:
        """Get LLM context string.

        Args:
            mode: "accessibility" (default) or "dom"
                - accessibility: Clean, filtered, role-based IDs (button-0)
                - dom: Complete, tag-based IDs (input-0), includes file inputs
        """
        if self._context_str is None:
            if mode == "accessibility":
                self._build_accessibility_context()
            elif mode == "dom":
                self._build_dom_context()
            else:
                raise ValueError(
                    f"Invalid mode: {mode}. Must be 'accessibility' or 'dom'"
                )

        return self._context_str

    def _build_accessibility_context(self) -> None:
        """Build context from accessibility tree."""
        # Filter accessibility tree
        filtered_root = filter_ignored_nodes(self.ax_root)
        if filtered_root is None:
            self._context_str = ""
            self._element_map = {}
            return

        filtered_root = filter_duplicate_text(filtered_root)
        if filtered_root is None:
            self._context_str = ""
            self._element_map = {}
            return

        filtered_root = filter_non_semantic_role(filtered_root)

        # Assign role-based IDs
        role_id_map = self._assign_role_ids(filtered_root)

        # Serialize
        self._context_str = self._serialize_accessibility_context(
            filtered_root, self.include_element_ids
        )

        # Build DOM lookup map
        dom_map: Dict[int, DomNode] = {}
        for node in self.dom_root.traverse():
            if isinstance(node, DomNode) and node.backend_dom_node_id is not None:
                dom_map[node.backend_dom_node_id] = node

        # Translate role IDs to DOM nodes
        self._element_map = {}
        for role_id, ax_node in role_id_map.items():
            if ax_node.backend_dom_node_id is not None:
                dom_node = dom_map.get(ax_node.backend_dom_node_id)
                if dom_node:
                    self._element_map[role_id] = dom_node

    def _build_dom_context(self) -> None:
        """Build context from DOM tree."""
        from ..dom.filters import filter_non_rendered, filter_non_semantic

        # Preserve original node references before filtering (for XPath computation)
        self._add_original_node_references(self.dom_root)

        # Filter DOM tree
        filtered_root = filter_non_rendered(self.dom_root)
        if filtered_root is None:
            self._context_str = ""
            self._element_map = {}
            return

        filtered_root = filter_non_semantic(filtered_root)
        if filtered_root is None:
            self._context_str = ""
            self._element_map = {}
            return

        # Assign tag-based IDs
        tag_map = self._assign_tag_ids(filtered_root)

        # Serialize
        self._context_str = self._serialize_dom_context(filtered_root)

        # Store tag map as interactive map
        self._element_map = tag_map

    def get_dom_node(self, id: str) -> Optional[DomNode]:
        """Get DOM node by element ID (role_id in accessibility mode, tag_id in DOM mode)."""
        if self._element_map is None:
            self.get_context()  # Trigger build
        return self._element_map.get(id)

    @staticmethod
    def _assign_role_ids(root: AXNode) -> Dict[str, AXNode]:
        """Assign role-based IDs (button-0, textbox-1) to accessibility tree nodes."""
        role_id_map = {}
        role_counters: Dict[str, int] = {}

        for node in root.traverse():
            role = str(node.role.value)
            count = role_counters.get(role, 0)
            role_id = f"{role}-{count}"
            node.metadata["role_id"] = role_id
            role_id_map[role_id] = node
            role_counters[role] = count + 1

        return role_id_map

    @staticmethod
    def _should_filter_url(url: str) -> bool:
        """Check if URL should be filtered from context.

        Filters out:
        - data:image URLs (very long base64-encoded images)
        - Other data URLs
        - Very long URLs (> 200 chars)
        """
        if not isinstance(url, str):
            return False

        # Filter data: URLs (especially data:image)
        if url.startswith("data:"):
            return True

        # Filter very long URLs
        if len(url) > 200:
            return True

        return False

    @staticmethod
    def _serialize_accessibility_context(
        root: AXNode, include_element_ids: bool
    ) -> str:
        """Serialize accessibility tree to markdown with role-based IDs."""
        lines = []

        def traverse(node: AXNode, depth: int = 0):
            indent = "  " * depth
            role = str(node.role.value)

            if role in ("StaticText", "InlineTextBox"):
                if node.name and node.name.value:
                    lines.append(f'{indent}- "{node.name.value}"')
                for child in node.children:
                    traverse(child, depth + 1)
                return

            role_id = node.metadata["role_id"]
            parts = [role_id] if include_element_ids else [role]

            if node.name and node.name.value:
                parts.append(f'"{node.name.value}"')

            if node.description and node.description.value:
                parts.append(f'description="{node.description.value}"')

            for prop in node.properties:
                prop_value = prop.value.value
                if prop_value is None:
                    continue

                if isinstance(prop_value, bool):
                    if prop_value:
                        parts.append(f"{prop.name}=true")
                elif isinstance(prop_value, (int, float)):
                    parts.append(f"{prop.name}={prop_value}")
                elif isinstance(prop_value, str) and prop_value:
                    # Skip data URLs and very long URLs
                    if LLMDomContext._should_filter_url(prop_value):
                        continue
                    parts.append(f"{prop.name}={prop_value}")

            lines.append(f"{indent}- {' '.join(parts)}")

            for child in node.children:
                traverse(child, depth + 1)

        traverse(root, 0)
        return "\n".join(lines)

    @staticmethod
    def _add_original_node_references(root: DomNode) -> None:
        """Add original_node reference to metadata before filtering."""
        for node in root.traverse():
            if isinstance(node, DomNode):
                node.metadata["original_node"] = node

    @staticmethod
    def _assign_tag_ids(root: DomNode) -> Dict[str, DomNode]:
        """Assign tag-based IDs (input-0, button-1) to DOM tree nodes.

        Returns mapping of tag_id -> original unfiltered node (for correct XPath).
        """
        tag_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if not isinstance(node, DomNode):
                continue

            tag = node.tag.lower()
            count = tag_counters.get(tag, 0)
            tag_id = f"{tag}-{count}"
            node.metadata["tag_id"] = tag_id

            # Store original node (not filtered) for correct XPath computation
            original_node = node.metadata.get("original_node", node)
            tag_map[tag_id] = original_node
            tag_counters[tag] = count + 1

        return tag_map

    @staticmethod
    def _serialize_dom_context(root: DomNode) -> str:
        """Serialize DOM tree to markdown with tag-based IDs."""
        from ..dom.domnode import Text

        lines = []

        def traverse(node: DomNode, depth: int = 0):
            # Handle text nodes
            if isinstance(node, Text):
                text = node.content.strip()
                if text:
                    indent = "  " * depth
                    lines.append(f'{indent}- "{text}"')
                return

            # Skip non-element nodes
            if not isinstance(node, DomNode):
                return

            indent = "  " * depth
            tag_id = node.metadata.get("tag_id", "unknown")
            parts = [tag_id]

            # Add attributes
            for attr_name, attr_value in node.attrib.items():
                if attr_value:
                    # Skip data URLs and very long URLs
                    if LLMDomContext._should_filter_url(attr_value):
                        continue
                    parts.append(f"{attr_name}={attr_value}")

            lines.append(f"{indent}- {' '.join(parts)}")

            # Traverse children
            for child in node.children:
                traverse(child, depth + 1)

        traverse(root, 0)
        return "\n".join(lines)
