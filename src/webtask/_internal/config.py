
import os


class Config:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Load environment variables once on first access
            debug_value = os.getenv("WEBTASK_DEBUG", "").lower()
            cls._instance._debug = debug_value in ("1", "true", "yes")
            cls._instance._debug_dir = os.getenv("WEBTASK_DEBUG_DIR", "debug")
            cls._instance._test_mode = os.getenv("WEBTASK_TEST_MODE")
        return cls._instance

    def is_debug_enabled(self) -> bool:
        return self._debug

    def get_debug_dir(self) -> str:
        return self._debug_dir

    def is_recording(self) -> bool:
        return self._test_mode == "record"

    def is_replaying(self) -> bool:
        return self._test_mode == "replay"
