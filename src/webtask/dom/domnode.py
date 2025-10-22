"""Core DOM node types with browser rendering data."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any


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

    def copy(self) -> 'DomNodeData':
        """Create a copy of this data."""
        return DomNodeData(
            tag=self.tag,
            attrib=self.attrib.copy(),
            styles=self.styles.copy(),
            bounds=self.bounds,
            metadata=self.metadata.copy(),
        )


@dataclass
class DomNode:
    """
    DOM element node with browser rendering data.

    Attributes:
        tag: Element tag name (e.g., 'div', 'button')
        attrib: Element attributes as key-value pairs
        styles: Computed CSS styles from browser
        bounds: Element bounding box (position and dimensions)
        metadata: Parser-specific metadata (e.g., backend_node_id, source_line)
        children: Child nodes (can be DomNode or Text)
        parent: Parent node reference
    """

    data: DomNodeData
    children: List[Union['DomNode', 'Text']] = field(default_factory=list)
    parent: Optional['DomNode'] = field(default=None, repr=False)

    def __init__(
        self,
        tag: str = None,
        attrib: Dict[str, str] = None,
        styles: Dict[str, str] = None,
        bounds: Optional[BoundingBox] = None,
        metadata: Dict[str, Any] = None,
        data: DomNodeData = None,
    ):
        """
        Create a DomNode.

        Can be created either by passing individual fields or a DomNodeData object.
        """
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
        """Element tag name."""
        return self.data.tag

    @property
    def attrib(self) -> Dict[str, str]:
        """Element attributes."""
        return self.data.attrib

    @attrib.setter
    def attrib(self, value: Dict[str, str]):
        """Set element attributes."""
        self.data.attrib = value

    @property
    def styles(self) -> Dict[str, str]:
        """Computed CSS styles."""
        return self.data.styles

    @property
    def bounds(self) -> Optional[BoundingBox]:
        """Element bounding box."""
        return self.data.bounds

    @property
    def metadata(self) -> Dict[str, Any]:
        """Parser-specific metadata."""
        return self.data.metadata

    def add_child(self, child: Union['DomNode', 'Text']):
        """Add a child node."""
        self.children.append(child)
        child.parent = self

    def copy(self) -> 'DomNode':
        """
        Create a shallow copy of this node (without children).

        Shares the same data reference (tag, attrib, styles, bounds, metadata).
        Only the tree structure (children, parent) is new.

        Returns:
            New DomNode with shared data and empty children list.
        """
        return DomNode(data=self.data)

    def deepcopy(self) -> 'DomNode':
        """
        Create a deep copy of this node (without children).

        Copies the data (tag, attrib, styles, bounds, metadata).
        Use this when you plan to modify the attributes or styles.

        Returns:
            New DomNode with copied data and empty children list.
        """
        return DomNode(data=self.data.copy())

    def is_visible(self) -> bool:
        """
        Check if element is visible based on computed styles.

        Returns False if:
        - display: none
        - visibility: hidden
        - opacity: 0
        """
        if self.styles.get('display') == 'none':
            return False
        if self.styles.get('visibility') == 'hidden':
            return False
        try:
            if float(self.styles.get('opacity', '1')) == 0:
                return False
        except (ValueError, TypeError):
            pass
        return True

    def has_zero_size(self) -> bool:
        """Check if element has zero width or height."""
        if not self.bounds:
            return False
        return self.bounds.width == 0 or self.bounds.height == 0

    def traverse(self):
        """
        Traverse the tree in depth-first order.

        Yields:
            DomNode and Text nodes in depth-first order (pre-order)

        Example:
            >>> for node in root.traverse():
            ...     if isinstance(node, Text):
            ...         print(node.content)
        """
        yield self
        for child in self.children:
            if isinstance(child, DomNode):
                yield from child.traverse()
            else:  # Text node
                yield child

    def get_text(self, separator: str = '') -> str:
        """
        Get all text content from this node and descendants.

        Args:
            separator: String to join text parts with

        Returns:
            Combined text content
        """
        parts = [node.content for node in self.traverse() if isinstance(node, Text)]
        return separator.join(parts)

    def get_x_path(self) -> 'XPath':
        """
        Get the absolute XPath from root to this element.

        Returns:
            XPath object (e.g., XPath('/html/body/div[1]/button[2]'))
        """
        from .selector import XPath

        if self.parent is None:
            # Root element
            return XPath(f'/{self.tag}')

        # Find the position among siblings with the same tag
        siblings = [child for child in self.parent.children
                   if isinstance(child, DomNode) and child.tag == self.tag]

        if len(siblings) == 1:
            # Only child with this tag, no index needed
            position = ''
        else:
            # Multiple siblings with same tag, add 1-based index
            index = siblings.index(self) + 1
            position = f'[{index}]'

        # Recursively build the path
        parent_path = self.parent.get_x_path()
        return XPath(f'{parent_path.path}/{self.tag}{position}')


@dataclass
class Text:
    """
    DOM text node.

    Attributes:
        content: Text content
        parent: Parent node reference
    """
    content: str
    parent: Optional[DomNode] = field(default=None, repr=False)

    def __str__(self):
        return self.content
