"""Recording browser wrappers for test recording and replay.

This package provides browser wrappers that can record interactions to fixture files
and replay them for deterministic, offline testing.
"""

from .browser import RecordingBrowser
from .session import RecordingSession
from .page import RecordingPage
from .element import RecordingElement

__all__ = [
    "RecordingBrowser",
    "RecordingSession",
    "RecordingPage",
    "RecordingElement",
]
