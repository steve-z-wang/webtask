"""Core DOM node types with browser rendering data."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Dict, Optional, Union, Any

if TYPE_CHECKING:
    from .selector import XPath


@dataclass
class BoundingBox:
    """Element bounding box from browser rendering."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class DomNodeData:
    """Data container for DOM node properties."""

    tag: str
    attrib: Dict[str, str] = field(default_factory=dict)
    styles: Dict[str, str] = field(default_factory=dict)
    bounds: Optional[BoundingBox] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "DomNodeData":
        return DomNodeData(
            tag=self.tag,
            attrib=self.attrib.copy(),
            styles=self.styles.copy(),
            bounds=self.bounds,
            metadata=self.metadata.copy(),
        )


@dataclass
class DomNode:
    """DOM element node with browser rendering data."""

    data: DomNodeData
    children: List[Union["DomNode", "Text"]] = field(default_factory=list)
    parent: Optional["DomNode"] = field(default=None, repr=False)

    def __init__(
        self,
        tag: str = None,
        attrib: Dict[str, str] = None,
        styles: Dict[str, str] = None,
        bounds: Optional[BoundingBox] = None,
        metadata: Dict[str, Any] = None,
        data: DomNodeData = None,
    ):
        if data is not None:
            self.data = data
        else:
            self.data = DomNodeData(
                tag=tag,
                attrib=attrib or {},
                styles=styles or {},
                bounds=bounds,
                metadata=metadata or {},
            )
        self.children = []
        self.parent = None

    @property
    def tag(self) -> str:
        return self.data.tag

    @property
    def attrib(self) -> Dict[str, str]:
        return self.data.attrib

    @attrib.setter
    def attrib(self, value: Dict[str, str]):
        self.data.attrib = value

    @property
    def styles(self) -> Dict[str, str]:
        return self.data.styles

    @property
    def bounds(self) -> Optional[BoundingBox]:
        return self.data.bounds

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.data.metadata

    def add_child(self, child: Union["DomNode", "Text"]):
        self.children.append(child)
        child.parent = self

    def copy(self) -> "DomNode":
        """Create shallow copy without children."""
        return DomNode(data=self.data)

    def deepcopy(self) -> "DomNode":
        """Create deep copy without children."""
        return DomNode(data=self.data.copy())

    def has_zero_size(self) -> bool:
        if not self.bounds:
            return False
        return self.bounds.width == 0 or self.bounds.height == 0

    def traverse(self):
        """Traverse tree depth-first."""
        yield self
        for child in self.children:
            if isinstance(child, DomNode):
                yield from child.traverse()
            else:
                yield child

    def get_text(self, separator: str = "") -> str:
        """Get all text content."""
        parts = [node.content for node in self.traverse() if isinstance(node, Text)]
        return separator.join(parts)

    def get_x_path(self) -> "XPath":
        """Get XPath to this element."""
        from .selector import XPath

        if self.parent is None:
            return XPath(f"/{self.tag}")

        siblings = [
            child
            for child in self.parent.children
            if isinstance(child, DomNode) and child.tag == self.tag
        ]

        if len(siblings) == 1:
            position = ""
        else:
            index = siblings.index(self) + 1
            position = f"[{index}]"

        parent_path = self.parent.get_x_path()
        return XPath(f"{parent_path.path}/{self.tag}{position}")


@dataclass
class Text:
    """DOM text node."""

    content: str
    parent: Optional[DomNode] = field(default=None, repr=False)

    def __str__(self):
        return self.content
