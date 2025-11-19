"""RecordingContext - Context wrapper for test recording and replay."""

import uuid
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from webtask.browser import Context

if TYPE_CHECKING:
    from .browser import RecordingBrowser


class RecordingContext(Context):
    """Context wrapper that records/replays interactions."""

    def __init__(
        self,
        browser: "RecordingBrowser",
        context: Optional[Context] = None,
        fixture_path: str = None,
        instance_id: str = None,
    ):
        self._browser = browser
        self._context = context
        self._fixture_path = Path(fixture_path) if fixture_path else None

        # Instance tracking - use provided ID or generate new UUID
        self._instance_id = instance_id or str(uuid.uuid4())
        self._call_index = 0

    @property
    def pages(self):
        """Get all pages in this context."""
        if self._browser._is_replaying:
            # In replay mode, pages aren't tracked
            return []
        return self._context.pages if self._context else []

    async def create_page(self):
        """Create a recording page."""
        from .page import RecordingPage

        if self._browser._is_replaying:
            result = self._get_next_result("create_page")
            page_id = result.get("page_instance_id")
            return RecordingPage(
                context=self,
                page=None,
                fixture_path=str(self._fixture_path),
                instance_id=page_id,
            )

        page = await self._context.create_page()
        recording_page = RecordingPage(
            context=self, page=page, fixture_path=str(self._fixture_path)
        )

        if self._browser._is_recording:
            self._record_call(
                "create_page", {}, {"page_instance_id": recording_page._instance_id}
            )

        return recording_page

    def _get_call_path(self, call_index: int):
        """Get path for a specific call file."""
        return (
            self._browser._fixture_path
            / f"session_{self._instance_id}"
            / f"call_{call_index:03d}.json"
        )

    def _record_call(self, method: str, args: dict, result):
        """Record a session method call."""
        call_data = {
            "class": "session",
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

    async def close(self):
        """Close the session."""
        if self._browser._is_replaying:
            return

        return await self._context.close()
