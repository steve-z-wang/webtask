"""RecordingElement - Element wrapper for test recording and replay."""

import uuid
from typing import Optional, Dict, List, Union, TYPE_CHECKING
from webtask.browser import Element

if TYPE_CHECKING:
    from .page import RecordingPage


class RecordingElement(Element):
    """Element wrapper that records/replays interactions."""

    def __init__(
        self,
        page: "RecordingPage",
        element: Optional[Element] = None,
        index: int = 0,
        instance_id: str = None,
    ):
        self._page = page
        self._element = element
        self._index = index  # Element index for replay matching

        # Instance tracking - use provided ID or generate new UUID
        self._instance_id = instance_id or str(uuid.uuid4())
        self._call_index = 0

    def _get_call_path(self, call_index: int):
        """Get path for a specific call file."""
        return (
            self._page._context._browser._fixture_path
            / f"element_{self._instance_id}"
            / f"call_{call_index:03d}.json"
        )

    def _record_call(self, method: str, args: dict, result):
        """Record an element method call."""
        call_data = {
            "class": "element",
            "instance_id": self._instance_id,
            "method": method,
            "args": args,
            "result": result,
        }
        call_path = self._get_call_path(self._call_index)
        call_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(call_path, "w") as f:
            json.dump(call_data, f, indent=2)

        self._call_index += 1

    def _get_next_result(self, method: str):
        """Get next recorded result."""
        call_path = self._get_call_path(self._call_index)

        import json

        with open(call_path, "r") as f:
            call = json.load(f)

        self._call_index += 1
        return call["result"]

    async def get_tag_name(self) -> str:
        """Get tag name."""
        if self._page._context._browser._is_replaying:
            return self._get_next_result("get_tag_name")

        result = await self._element.get_tag_name()

        if self._page._context._browser._is_recording:
            self._record_call("get_tag_name", {}, result)

        return result

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get attribute."""
        if self._page._context._browser._is_replaying:
            return self._get_next_result("get_attribute")

        result = await self._element.get_attribute(name)

        if self._page._context._browser._is_recording:
            self._record_call("get_attribute", {"name": name}, result)

        return result

    async def get_attributes(self) -> Dict[str, str]:
        """Get all attributes."""
        if self._page._context._browser._is_replaying:
            return self._get_next_result("get_attributes")

        result = await self._element.get_attributes()

        if self._page._context._browser._is_recording:
            self._record_call("get_attributes", {}, result)

        return result

    async def get_html(self, outer: bool = True) -> str:
        """Get HTML."""
        if self._page._context._browser._is_replaying:
            return self._get_next_result("get_html")

        result = await self._element.get_html(outer)

        if self._page._context._browser._is_recording:
            self._record_call("get_html", {"outer": outer}, result)

        return result

    async def get_parent(self) -> Optional[Element]:
        """Get parent element."""
        if self._page._context._browser._is_replaying:
            result = self._get_next_result("get_parent")
            return (
                RecordingElement(
                    page=self._page,
                    element=None,
                    index=-1,
                    instance_id=result["parent_instance_id"],
                )
                if result
                else None
            )

        parent = await self._element.get_parent()
        recording_parent = (
            RecordingElement(page=self._page, element=parent, index=-1)
            if parent
            else None
        )

        if self._page._context._browser._is_recording:
            self._record_call(
                "get_parent",
                {},
                (
                    {"parent_instance_id": recording_parent._instance_id}
                    if recording_parent
                    else None
                ),
            )

        return recording_parent

    async def get_children(self) -> List[Element]:
        """Get child elements."""
        if self._page._context._browser._is_replaying:
            result = self._get_next_result("get_children")
            return [
                RecordingElement(
                    page=self._page, element=None, index=i, instance_id=child_id
                )
                for i, child_id in enumerate(result["child_instance_ids"])
            ]

        children = await self._element.get_children()
        recording_children = [
            RecordingElement(page=self._page, element=child, index=i)
            for i, child in enumerate(children)
        ]

        if self._page._context._browser._is_recording:
            self._record_call(
                "get_children",
                {},
                {
                    "child_instance_ids": [
                        child._instance_id for child in recording_children
                    ]
                },
            )

        return recording_children

    async def click(self):
        """Click element."""
        if self._page._context._browser._is_replaying:
            self._get_next_result("click")
            return

        result = await self._element.click()

        if self._page._context._browser._is_recording:
            self._record_call("click", {}, None)

        return result

    async def fill(self, text: str):
        """Fill element."""
        if self._page._context._browser._is_replaying:
            self._get_next_result("fill")
            return

        result = await self._element.fill(text)

        if self._page._context._browser._is_recording:
            self._record_call("fill", {"text": text}, None)

        return result

    async def type(self, text: str, delay: float = None):
        """Type into element."""
        if self._page._context._browser._is_replaying:
            self._get_next_result("type")
            return

        result = await self._element.type(text, delay)

        if self._page._context._browser._is_recording:
            self._record_call("type", {"text": text, "delay": delay}, None)

        return result

    async def upload_file(self, file_path: Union[str, List[str]]):
        """Upload file(s)."""
        if self._page._context._browser._is_replaying:
            self._get_next_result("upload_file")
            return

        result = await self._element.upload_file(file_path)

        if self._page._context._browser._is_recording:
            self._record_call(
                "upload_file",
                {
                    "file_path": (
                        file_path if isinstance(file_path, list) else [file_path]
                    )
                },
                None,
            )

        return result
