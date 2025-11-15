"""LLMDomContext - builds LLM context with interactive_id → DomNode lookup."""

from typing import Dict, Optional, TYPE_CHECKING
from ..cdp import DomNode, AXNode
from ..cdp.accessibility.filters import (
    filter_ignored_nodes,
    filter_duplicate_names,
    filter_generic_nodes,
    filter_none_nodes,
)

if TYPE_CHECKING:
    from ...browser.page import Page


class LLMDomContext:
    """Builds LLM context from DOM and accessibility trees."""

    def __init__(
        self, dom_root: DomNode, ax_root: AXNode, include_interactive_ids: bool = True
    ):
        self.dom_root = dom_root
        self.ax_root = ax_root
        self.include_interactive_ids = include_interactive_ids
        self._context_str: Optional[str] = None
        self._interactive_map: Optional[Dict[str, DomNode]] = None

    @classmethod
    async def from_page(
        cls, page: "Page", include_interactive_ids: bool = True
    ) -> "LLMDomContext":
        """Create LLMDomContext from page."""
        dom_root = DomNode.from_cdp(await page.get_cdp_dom_snapshot())
        ax_root = AXNode.from_cdp(await page.get_cdp_accessibility_tree())
        return cls(
            dom_root=dom_root,
            ax_root=ax_root,
            include_interactive_ids=include_interactive_ids,
        )

    def get_context(self) -> str:
        """Get LLM context string."""
        if self._context_str is None:

            # Filter accessibility tree
            filtered_root = filter_ignored_nodes(self.ax_root)
            if filtered_root is None:
                self._context_str = ""
                self._interactive_map = {}
                return self._context_str

            filtered_root = filter_duplicate_names(filtered_root)
            if filtered_root is None:
                self._context_str = ""
                self._interactive_map = {}
                return self._context_str

            filtered_root = filter_generic_nodes(filtered_root)
            filtered_root = filter_none_nodes(filtered_root)

            # Assign interactive IDs
            ax_interactive_map = self._assign_interactive_ids(filtered_root)

            # Serialize
            self._context_str = self._serialize_context(
                filtered_root, self.include_interactive_ids
            )

            # Build DOM lookup map
            dom_map: Dict[int, DomNode] = {}
            for node in self.dom_root.traverse():
                if isinstance(node, DomNode) and node.backend_dom_node_id is not None:
                    dom_map[node.backend_dom_node_id] = node

            # Translate to DOM nodes
            self._interactive_map = {}
            for interactive_id, ax_node in ax_interactive_map.items():
                if ax_node.backend_dom_node_id is not None:
                    dom_node = dom_map.get(ax_node.backend_dom_node_id)
                    if dom_node:
                        self._interactive_map[interactive_id] = dom_node

        return self._context_str

    def get_dom_node(self, interactive_id: str) -> Optional[DomNode]:
        """Get DOM node by interactive ID."""
        if self._interactive_map is None:
            self.get_context()  # Trigger build
        return self._interactive_map.get(interactive_id)

    @staticmethod
    def _assign_interactive_ids(root: AXNode) -> Dict[str, AXNode]:
        interactive_map = {}
        role_counters: Dict[str, int] = {}

        for node in root.traverse():
            role = str(node.role.value)
            count = role_counters.get(role, 0)
            interactive_id = f"{role}-{count}"
            node.metadata["interactive_id"] = interactive_id
            interactive_map[interactive_id] = node
            role_counters[role] = count + 1

        return interactive_map

    @staticmethod
    def _serialize_context(root: AXNode, include_interactive_ids: bool) -> str:
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

            interactive_id = node.metadata["interactive_id"]
            parts = [interactive_id] if include_interactive_ids else [role]

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
                    parts.append(f"{prop.name}={prop_value}")

            lines.append(f"{indent}- {' '.join(parts)}")

            for child in node.children:
                traverse(child, depth + 1)

        traverse(root, 0)
        return "\n".join(lines)
