
from typing import Dict, Optional
from pathlib import Path
from webtask.browser import Page
from ..dom.domnode import DomNode, Text
from ..dom_processing.filters import filter_non_rendered, filter_non_semantic
from ..config import Config


class DomContextBuilder:

    @staticmethod
    async def build_context(
        page: Page, include_element_ids: bool = True, debug_filename: Optional[str] = None
    ) -> tuple[Optional[str], Dict[str, DomNode]]:
        snapshot = await page.get_snapshot()
        root = snapshot.root

        # Save raw unfiltered HTML if debug enabled
        if Config().is_debug_enabled() and debug_filename:
            raw_html = DomContextBuilder._serialize_context(root, include_element_ids=False)
            debug_dir = Path(Config().get_debug_dir())
            debug_dir.mkdir(parents=True, exist_ok=True)
            raw_html_path = debug_dir / f"{debug_filename}_raw_dom.txt"
            with open(raw_html_path, "w") as f:
                f.write(raw_html)

        # Add reference to original nodes before filtering
        root = DomContextBuilder._add_node_reference(root)

        # Apply filters
        root = filter_non_rendered(root)
        if root is None:
            return None, {}

        root = filter_non_semantic(root)
        if root is None:
            return None, {}

        # Always assign element IDs (needed for element_map)
        element_map = DomContextBuilder._assign_element_ids(root)

        # Serialize with or without element IDs
        context_str = DomContextBuilder._serialize_context(
            root, include_element_ids=include_element_ids
        )

        return context_str, element_map

    @staticmethod
    def _assign_element_ids(root: DomNode) -> Dict[str, DomNode]:
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
    def _serialize_context(root: DomNode, include_element_ids: bool = True) -> str:
        lines = []

        def traverse(n: DomNode, depth: int = 0):
            indent = "  " * depth

            # Use element_id if available and include_element_ids=True, otherwise use tag
            if include_element_ids:
                display_name = n.metadata.get("element_id", n.tag)
            else:
                display_name = n.tag

            attr_parts = []
            if n.attrib:
                attr_strs = [f'{k}="{v}"' for k, v in n.attrib.items()]
                attr_parts.append(f'({" ".join(attr_strs)})')

            markdown = f"{display_name}"
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
        for node in root.traverse():
            if isinstance(node, DomNode):
                node.metadata["original_node"] = node

        return root
