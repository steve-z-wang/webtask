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
        return cls._instance

    def is_debug_enabled(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if WEBTASK_DEBUG is set to a truthy value
        """
        return self._debug

    def get_debug_dir(self) -> str:
        """
        Get the debug output directory.

        Returns:
            Path to debug directory (default: "debug")
        """
        return self._debug_dir
