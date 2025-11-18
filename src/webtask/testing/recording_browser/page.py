"""RecordingPage - Page wrapper for test recording and replay."""

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
from webtask.browser import Page, Element

if TYPE_CHECKING:
    from .context import RecordingContext


class RecordingPage(Page):
    """Page wrapper that records/replays interactions."""

    def __init__(
        self,
        context: "RecordingContext",
        page: Optional[Page] = None,
        fixture_path: str = None,
        instance_id: str = None,
    ):
        self._context = context
        self._page = page
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._current_url = ""

        # Instance tracking - use provided ID or generate new UUID
        self._instance_id = instance_id or str(uuid.uuid4())
        self._call_index = 0

    async def navigate(self, url: str):
        """Navigate to URL."""
        if self._context._browser._is_replaying:
            self._current_url = url
            self._get_next_result("navigate")
            return

        result = await self._page.navigate(url)
        self._current_url = url

        if self._context._browser._is_recording:
            self._record_call("navigate", {"url": url}, None)

        return result

    async def get_cdp_dom_snapshot(self) -> Dict[str, Any]:
        """Get CDP DOM snapshot."""
        if self._context._browser._is_replaying:
            return self._get_next_result("get_cdp_dom_snapshot")

        result = await self._page.get_cdp_dom_snapshot()

        if self._context._browser._is_recording:
            self._record_call("get_cdp_dom_snapshot", {}, result)

        return result

    async def get_cdp_accessibility_tree(self) -> Dict[str, Any]:
        """Get CDP accessibility tree."""
        if self._context._browser._is_replaying:
            return self._get_next_result("get_cdp_accessibility_tree")

        result = await self._page.get_cdp_accessibility_tree()

        if self._context._browser._is_recording:
            self._record_call("get_cdp_accessibility_tree", {}, result)

        return result

    def _get_call_path(self, call_index: int):
        """Get path for a specific call file."""
        return (
            self._context._browser._fixture_path
            / f"page_{self._instance_id}"
            / f"call_{call_index:03d}.json"
        )

    def _record_call(self, method: str, args: dict, result):
        """Record a page method call."""
        call_data = {
            "class": "page",
            "instance_id": self._instance_id,
            "method": method,
            "args": args,
            "result": result,
        }
        call_path = self._get_call_path(self._call_index)
        call_path.parent.mkdir(parents=True, exist_ok=True)

        with open(call_path, "w") as f:
            json.dump(call_data, f, indent=2)

        self._call_index += 1

    def _get_next_result(self, method: str):
        """Get next recorded result."""
        call_path = self._get_call_path(self._call_index)

        with open(call_path, "r") as f:
            call = json.load(f)

        self._call_index += 1
        return call["result"]

    async def select(self, selector) -> List[Element]:
        """Select elements."""
        from .element import RecordingElement
        from webtask._internal.dom.selector import XPath

        # Convert XPath to string for JSON serialization
        selector_str = selector.path if isinstance(selector, XPath) else str(selector)

        if self._context._browser._is_replaying:
            result = self._get_next_result("select")
            # Return list of RecordingElements with their instance IDs
            return [
                RecordingElement(page=self, element=None, index=i, instance_id=elem_id)
                for i, elem_id in enumerate(result["element_instance_ids"])
            ]

        elements = await self._page.select(selector)
        recording_elements = [
            RecordingElement(page=self, element=elem, index=i)
            for i, elem in enumerate(elements)
        ]

        if self._context._browser._is_recording:
            self._record_call(
                "select",
                {"selector": selector_str},
                {
                    "element_instance_ids": [
                        elem._instance_id for elem in recording_elements
                    ]
                },
            )

        return recording_elements

    async def select_one(self, selector) -> Element:
        """Select single element."""
        from .element import RecordingElement
        from webtask._internal.dom.selector import XPath

        # Convert XPath to string for JSON serialization
        selector_str = selector.path if isinstance(selector, XPath) else str(selector)

        if self._context._browser._is_replaying:
            result = self._get_next_result("select_one")
            return RecordingElement(
                page=self,
                element=None,
                index=0,
                instance_id=result["element_instance_id"],
            )

        element = await self._page.select_one(selector)
        recording_element = RecordingElement(page=self, element=element, index=0)

        if self._context._browser._is_recording:
            self._record_call(
                "select_one",
                {"selector": selector_str},
                {"element_instance_id": recording_element._instance_id},
            )

        return recording_element

    async def close(self):
        """Close the page."""
        if self._context._browser._is_replaying:
            return

        return await self._page.close()

    async def wait_for_load(self, timeout: int = 10000):
        """Wait for page to fully load."""
        if self._context._browser._is_replaying:
            self._get_next_result("wait_for_load")
            return

        result = await self._page.wait_for_load(timeout)

        if self._context._browser._is_recording:
            self._record_call("wait_for_load", {"timeout": timeout}, None)

        return result

    async def screenshot(
        self, path: Optional[Union[str, Path]] = None, full_page: bool = False
    ) -> bytes:
        """Take screenshot."""
        if self._context._browser._is_replaying:
            # Return base64-decoded bytes from recording
            import base64

            result = self._get_next_result("screenshot")
            return base64.b64decode(result["data"])

        result = await self._page.screenshot(path, full_page)

        if self._context._browser._is_recording:
            import base64

            # Encode bytes to base64 for JSON storage
            self._record_call(
                "screenshot",
                {"path": str(path) if path else None, "full_page": full_page},
                {"data": base64.b64encode(result).decode("utf-8")},
            )

        return result

    async def keyboard_type(
        self, text: str, clear: bool = False, delay: float = 80
    ) -> None:
        """Type text."""
        if self._context._browser._is_replaying:
            self._get_next_result("keyboard_type")
            return

        result = await self._page.keyboard_type(text, clear, delay)

        if self._context._browser._is_recording:
            self._record_call(
                "keyboard_type", {"text": text, "clear": clear, "delay": delay}, None
            )

        return result

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript."""
        if self._context._browser._is_replaying:
            return self._get_next_result("evaluate")

        result = await self._page.evaluate(script)

        if self._context._browser._is_recording:
            self._record_call("evaluate", {"script": script}, result)

        return result

    @property
    def url(self) -> str:
        """Get current URL."""
        if self._context._browser._is_replaying:
            return self._current_url

        return self._page.url
