"""DOM snapshot with metadata."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .domnode import DomNode
from .parsers import parse_cdp


@dataclass
class DomSnapshot:
    """
    DOM snapshot with metadata.

    Pure data structure capturing a snapshot of the DOM at a specific point in time.
    """

    root: DomNode
    url: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cdp(cls, cdp_snapshot: Dict[str, Any], url: Optional[str] = None) -> 'DomSnapshot':
        """
        Create DomSnapshot from CDP (Chrome DevTools Protocol) snapshot.

        Args:
            cdp_snapshot: CDP DOMSnapshot.captureSnapshot response
            url: Optional URL of the page

        Returns:
            DomSnapshot instance with parsed DOM tree
        """
        root = parse_cdp(cdp_snapshot)
        return cls(root=root, url=url)
