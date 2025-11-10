"""RecordingLLM - LLM wrapper for test recording and replay."""

import json
import uuid
from pathlib import Path
from typing import List, Optional
from webtask.llm import LLM, Content, Text, Image
from webtask._internal.config import Config


class RecordingLLM(LLM):
    """
    LLM wrapper that records/replays interactions for testing.

    Modes (controlled by WEBTASK_TEST_MODE env var):
    - record: Delegates to real LLM and saves each call to separate file
    - replay: Returns saved responses from fixture files in order
    - live (default): Delegates to real LLM without recording

    Fixture Format:
        Each LLM instance has its own UUID-based directory:
        fixtures/shopping_cart/
            llm_abc123/
                call_000.json
                call_001.json

    Example:
        # Record mode (WEBTASK_TEST_MODE=record)
        llm = RecordingLLM(
            GeminiLLM.create(...),
            fixture_path="tests/e2e/fixtures/shopping_cart/"
        )

        # Replay mode (WEBTASK_TEST_MODE=replay)
        llm = RecordingLLM(
            fixture_path="tests/e2e/fixtures/shopping_cart/",
            instance_id="abc123"  # UUID from recording
        )
    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        fixture_path: str = None,
        instance_id: str = None,
    ):
        """
        Initialize RecordingLLM.

        Args:
            llm: Real LLM to wrap (required for record and live modes)
            fixture_path: Path to fixture directory (not a file!)
            instance_id: Instance ID for replay (generated if not provided)
        """
        super().__init__()
        self._llm = llm
        self._fixture_path = Path(fixture_path) if fixture_path else None

        # Instance tracking - use provided ID or generate new UUID
        self._instance_id = instance_id or str(uuid.uuid4())
        self._call_index = 0
        self._total_calls = 0  # Track how many calls we've made

        config = Config()
        self._is_recording = config.is_recording()
        self._is_replaying = config.is_replaying()

        # Validate configuration
        if self._is_recording or (not self._is_recording and not self._is_replaying):
            if not self._llm:
                raise ValueError("llm parameter required for record/live mode")

        if self._is_recording or self._is_replaying:
            if not self._fixture_path:
                raise ValueError("fixture_path required for record/replay mode")

        # Load fixture count if replaying
        if self._is_replaying:
            self._load_fixture_count()

    def _serialize_content(self, content: List[Content]) -> List[dict]:
        """Serialize Content list to JSON-compatible dicts."""
        result = []
        for item in content:
            if isinstance(item, Text):
                result.append({"type": "text", "data": item.model_dump()})
            elif isinstance(item, Image):
                result.append({"type": "image", "data": item.model_dump()})
        return result

    def _deserialize_content(self, data: List[dict]) -> List[Content]:
        """Deserialize JSON dicts to Content list."""
        result = []
        for item in data:
            if item["type"] == "text":
                result.append(Text.model_validate(item["data"]))
            elif item["type"] == "image":
                result.append(Image.model_validate(item["data"]))
        return result

    def _load_fixture_count(self):
        """Count how many fixture files exist for this instance."""
        instance_dir = self._fixture_path / f"llm_{self._instance_id}"
        if not instance_dir.exists():
            raise FileNotFoundError(
                f"LLM fixture directory not found: {instance_dir}\n"
                f"Run test in record mode first: WEBTASK_TEST_MODE=record pytest ..."
            )

        # Count call_*.json files for this instance
        call_files = sorted(instance_dir.glob("call_*.json"))
        self._total_calls = len(call_files)
        self.logger.info(
            f"Found {self._total_calls} LLM call fixtures in {instance_dir}"
        )

    def _get_call_path(self, call_index: int) -> Path:
        """Get path for a specific call file."""
        return (
            self._fixture_path
            / f"llm_{self._instance_id}"
            / f"call_{call_index:03d}.json"
        )

    def _save_call(self, call_data: dict):
        """Save a single call to its own file."""
        call_path = self._get_call_path(self._call_index)
        call_path.parent.mkdir(parents=True, exist_ok=True)

        with open(call_path, "w") as f:
            json.dump(call_data, f, indent=2)

        self.logger.info(f"Saved LLM call {self._call_index} to {call_path}")

    def _load_call(self, call_index: int) -> dict:
        """Load a single call from its file."""
        call_path = self._get_call_path(call_index)

        if not call_path.exists():
            raise FileNotFoundError(
                f"LLM call fixture not found: {call_path}\n"
                f"Expected call {call_index} but only {self._total_calls} calls recorded.\n"
                f"Run test in record mode first: WEBTASK_TEST_MODE=record pytest ..."
            )

        with open(call_path, "r") as f:
            return json.load(f)

    async def generate(
        self, system: str, content: List[Content], use_json: bool = False
    ) -> str:
        """
        Generate text response (recording/replaying based on mode).

        Args:
            system: System prompt
            content: Content list
            use_json: Whether to use JSON mode

        Returns:
            Generated text response
        """
        if self._is_replaying:
            # Replay mode: load and return saved response
            if self._call_index >= self._total_calls:
                raise RuntimeError(
                    f"Replay error: Expected {self._call_index + 1} calls but only {self._total_calls} recorded"
                )

            call = self._load_call(self._call_index)
            self._call_index += 1

            self.logger.info(
                f"Replaying LLM call {self._call_index}/{self._total_calls}"
            )
            return call["response"]

        elif self._is_recording:
            # Record mode: call real LLM and save immediately
            response = await self._llm.generate(system, content, use_json)

            call_data = {
                "request": {
                    "system": system,
                    "content": self._serialize_content(content),
                    "use_json": use_json,
                },
                "response": response,
            }

            self._save_call(call_data)
            self._call_index += 1

            self.logger.info(f"Recorded LLM call {self._call_index}")
            return response

        else:
            # Live mode: just delegate
            return await self._llm.generate(system, content, use_json)
