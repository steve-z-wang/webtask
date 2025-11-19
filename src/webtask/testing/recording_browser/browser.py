"""RecordingBrowser - Browser wrapper for test recording and replay."""

import json
import uuid
from pathlib import Path
from typing import Optional, Any
from webtask.browser import Browser
from webtask._internal.config import Config


class RecordingBrowser(Browser):
    """
    Browser wrapper that records/replays interactions for testing.

    Modes (controlled by WEBTASK_TEST_MODE env var):
    - record: Delegates to real browser and saves each call to separate file
    - replay: Returns saved responses from fixture files in order
    - live (default): Delegates to real browser without recording

    Fixture Format:
        Each instance has its own UUID-based directory:
        fixtures/browser/test_name/
            browser_abc123/
                call_000.json
                call_001.json
            session_def456/
                call_000.json
            page_ghi789/
                call_000.json
            element_jkl012/
                call_000.json
    """

    def __init__(
        self,
        browser: Optional[Browser] = None,
        fixture_path: str = None,
        instance_id: str = None,
    ):
        """
        Initialize RecordingBrowser.

        Args:
            browser: Real browser to wrap (required for record and live modes)
            fixture_path: Path to fixture directory (not a file!)
            instance_id: Instance ID for replay (generated if not provided)
        """
        super().__init__(headless=browser.headless if browser else True)
        self._browser = browser
        self._fixture_path = Path(fixture_path) if fixture_path else None

        # Instance tracking - use provided ID or generate new UUID
        self._instance_id = instance_id or str(uuid.uuid4())

        self._call_index = 0  # Instance-specific counter
        self._total_calls = 0

        config = Config()
        self._is_recording = config.is_recording()
        self._is_replaying = config.is_replaying()

        # Validate configuration
        if self._is_recording or (not self._is_recording and not self._is_replaying):
            if not self._browser:
                raise ValueError("browser parameter required for record/live mode")

        if self._is_recording or self._is_replaying:
            if not self._fixture_path:
                raise ValueError("fixture_path required for record/replay mode")

        # Load fixture count if replaying
        if self._is_replaying:
            self._load_fixture_count()

    def _load_fixture_count(self):
        """Count how many fixture files exist for this instance."""
        instance_dir = self._fixture_path / f"browser_{self._instance_id}"
        if not instance_dir.exists():
            raise FileNotFoundError(
                f"Browser fixture directory not found: {instance_dir}\n"
                f"Run test in record mode first: WEBTASK_TEST_MODE=record pytest ..."
            )

        # Count call_*.json files for this instance
        call_files = sorted(instance_dir.glob("call_*.json"))
        self._total_calls = len(call_files)

    def _get_call_path(self, call_index: int) -> Path:
        """Get path for a specific call file."""
        return (
            self._fixture_path
            / f"browser_{self._instance_id}"
            / f"call_{call_index:03d}.json"
        )

    def _save_call(self, call_data: dict):
        """Save a single call to its own file."""
        call_path = self._get_call_path(self._call_index)
        call_path.parent.mkdir(parents=True, exist_ok=True)

        # Add class and instance metadata
        call_data["class"] = "browser"
        call_data["instance_id"] = self._instance_id

        with open(call_path, "w") as f:
            json.dump(call_data, f, indent=2)

    def _load_call(self, call_index: int) -> dict:
        """Load a single call from its file."""
        call_path = self._get_call_path(call_index)

        if not call_path.exists():
            raise FileNotFoundError(
                f"Browser call fixture not found: {call_path}\n"
                f"Expected call {call_index} but only {self._total_calls} calls recorded.\n"
                f"Run test in record mode first: WEBTASK_TEST_MODE=record pytest ..."
            )

        with open(call_path, "r") as f:
            return json.load(f)

    def _record_call(self, method: str, args: dict, result: Any):
        """Record a method call and save immediately."""
        call_data = {"method": method, "args": args, "result": result}
        self._save_call(call_data)
        self._call_index += 1

    def _get_next_result(self, method: str):
        """Get next recorded result."""
        if self._call_index >= self._total_calls:
            raise RuntimeError(
                f"Replay error: Expected {self._call_index + 1} calls but only {self._total_calls} recorded"
            )

        call = self._load_call(self._call_index)
        if call["method"] != method:
            raise RuntimeError(
                f"Replay error: Expected method '{call['method']}' but got '{method}' at call {self._call_index}"
            )

        self._call_index += 1
        return call["result"]

    @classmethod
    async def create(cls, **kwargs):
        """Create browser (not used with RecordingBrowser - use __init__ directly)."""
        raise NotImplementedError("Use RecordingBrowser(...) directly instead")

    @classmethod
    async def connect(cls, **kwargs):
        """Connect to browser (not used with RecordingBrowser - use __init__ directly)."""
        raise NotImplementedError("Use RecordingBrowser(...) directly instead")

    @property
    def contexts(self):
        """Get all browser contexts."""
        if self._is_replaying:
            # In replay mode, contexts aren't tracked
            return []
        return self._browser.contexts if self._browser else []

    async def create_context(self, **kwargs):
        """Create a recording context."""
        from .context import RecordingContext

        if self._is_replaying:
            result = self._get_next_result("create_context")
            context_id = result.get("context_instance_id")
            return RecordingContext(
                browser=self,
                context=None,
                fixture_path=str(self._fixture_path),
                instance_id=context_id,
            )

        context = await self._browser.create_context(**kwargs)
        recording_context = RecordingContext(
            browser=self, context=context, fixture_path=str(self._fixture_path)
        )

        if self._is_recording:
            self._record_call(
                "create_context",
                kwargs,
                {"context_instance_id": recording_context._instance_id},
            )

        return recording_context

    async def close(self):
        """Close the browser."""
        if self._is_replaying:
            self._get_next_result("close")
            return

        result = await self._browser.close()

        if self._is_recording:
            self._record_call("close", {}, None)

        return result
