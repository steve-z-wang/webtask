"""Internal configuration management for webtask."""

import os


class Config:
    """
    Singleton configuration loaded from environment variables.

    Environment variables are read once on first access (lazy loading).

    Environment variables:
        WEBTASK_DEBUG: Enable debug mode (saves screenshots and context)
                      Values: 1, true, True, yes
        WEBTASK_DEBUG_DIR: Directory for debug output (default: "debug")
                          Example: "debug/test_case_42"
        WEBTASK_TEST_MODE: Test recording/replay mode
                          Values: "record", "replay", or unset for live mode

    Usage:
        from webtask._internal.config import Config

        if Config().is_debug_enabled():
            debug_dir = Config().get_debug_dir()
            # Save debug info to debug_dir
    """

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
        """
        Check if debug mode is enabled.
        """
        return self._debug

    def get_debug_dir(self) -> str:
        """
        Get the debug output directory.
        """
        return self._debug_dir

    def is_recording(self) -> bool:
        """
        Check if test recording mode is enabled.
        """
        return self._test_mode == "record"

    def is_replaying(self) -> bool:
        """
        Check if test replay mode is enabled.
        """
        return self._test_mode == "replay"
