"""LLMBrowser - bridges LLM text interface with browser operations."""

from typing import Dict
from ..browser import Page, Element
from ..dom.filters import apply_visibility_filters, apply_semantic_filters
from ..dom.utils import add_node_reference
from ..dom.domnode import DomNode
from ..llm import Block, LLM


class LLMBrowser:
    """
    Bridges LLM text interface with browser operations.

    Provides context with element IDs and executes actions by converting IDs to selectors.
    """

    def __init__(self, page: Page, llm: LLM):
        """
        Initialize with Page and LLM.

        Args:
            page: Page instance to wrap
            llm: LLM instance for natural language selection
        """
        self.page = page
        self.llm = llm
        self.element_map: Dict[str, DomNode] = {}

    async def to_context_block(self) -> Block:
        """
        Get formatted page context with element IDs for LLM.

        Returns:
            Block with formatted DOM
        """
        # Get raw snapshot from page
        snapshot = await self.page.get_snapshot()
        root = snapshot.root

        # Add node references (before filtering)
        root = add_node_reference(root)

        # Apply filters
        root = apply_visibility_filters(root)
        root = apply_semantic_filters(root)

        # Assign element IDs and build mapping
        self.element_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if isinstance(node, DomNode):
                tag = node.tag
                count = tag_counters.get(tag, 0)
                element_id = f"{tag}-{count}"

                node.metadata['element_id'] = element_id
                self.element_map[element_id] = node

                tag_counters[tag] = count + 1

        # Serialize to markdown
        from ..dom.serializers import serialize_to_markdown
        lines = []

        if snapshot.url:
            lines.append(f"URL: {snapshot.url}")
            lines.append("")

        lines.append(serialize_to_markdown(root))

        return Block("\n".join(lines))

    def _get_selector(self, element_id: str):
        """
        Convert element ID to selector (XPath or CSS).

        Args:
            element_id: Element ID (e.g., 'div-0', 'button-1')

        Returns:
            XPath object or CSS selector string

        Raises:
            KeyError: If element ID not found
        """
        if element_id not in self.element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        node = self.element_map[element_id]
        # Get the original unfiltered node to compute XPath from the full DOM tree
        original_node = node.metadata.get('original_node', node)
        # Use XPath for now (could be CSS selector in future)
        return original_node.get_x_path()

    async def navigate(self, url: str) -> None:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to
        """
        await self.page.navigate(url)

    async def click(self, element_id: str) -> None:
        """
        Click element by ID.

        Args:
            element_id: Element ID from context (e.g., 'button-0')

        Raises:
            KeyError: If element ID not found
        """
        selector = self._get_selector(element_id)
        element = await self.page.select_one(selector)
        await element.click()

    async def fill(self, element_id: str, value: str) -> None:
        """
        Fill element by ID with value.

        Args:
            element_id: Element ID from context (e.g., 'input-0')
            value: Value to fill

        Raises:
            KeyError: If element ID not found
        """
        selector = self._get_selector(element_id)
        element = await self.page.select_one(selector)
        await element.fill(value)

    async def type(self, element_id: str, text: str, delay: float = 80) -> None:
        """
        Type text into element by ID character by character.

        Simulates realistic keyboard input with delays between keystrokes.

        Args:
            element_id: Element ID from context (e.g., 'input-0')
            text: Text to type
            delay: Delay between keystrokes in milliseconds (default: 80ms)

        Raises:
            KeyError: If element ID not found
        """
        selector = self._get_selector(element_id)
        element = await self.page.select_one(selector)
        await element.type(text, delay=delay)

    async def select(self, description: str) -> Element:
        """
        Select element by natural language description.

        Uses LLM to find the element_id that matches the description,
        then converts it to a selector and returns the browser Element.

        Args:
            description: Natural language description of element

        Returns:
            Browser Element instance

        Raises:
            ValueError: If LLM fails to find a matching element
        """
        from .selector import NaturalSelector

        selector = NaturalSelector(self.llm, self)
        return await selector.select(description)
