"""DOM snapshot with metadata."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .domnode import DomNode
from .parsers import parse_cdp


@dataclass
class DomSnapshot:
    """DOM snapshot with metadata."""

    root: DomNode
    url: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cdp(
        cls, cdp_snapshot: Dict[str, Any], url: Optional[str] = None
    ) -> "DomSnapshot":
        """Create DomSnapshot from CDP snapshot."""
        root = parse_cdp(cdp_snapshot)
        return cls(root=root, url=url)
