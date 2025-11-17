"""Tests for CDP snapshot parser."""

import pytest
from webtask._internal.dom.parsers.cdp import (
    _get_string_resolver,
    _parse_layout_data,
    _create_element_nodes,
    _add_text_nodes,
    _build_tree,
    parse_cdp,
)
from webtask._internal.dom.domnode import DomNode, Text, BoundingBox


@pytest.mark.unit
class TestGetStringResolver:
    """Tests for _get_string_resolver function."""

    def test_resolves_valid_index(self):
        """Test resolving valid string index."""
        strings = ["hello", "world", "test"]
        resolve = _get_string_resolver(strings)

        assert resolve(0) == "hello"
        assert resolve(1) == "world"
        assert resolve(2) == "test"

    def test_returns_empty_for_invalid_index(self):
        """Test returns empty string for invalid index."""
        strings = ["hello", "world"]
        resolve = _get_string_resolver(strings)

        assert resolve(-1) == ""
        assert resolve(10) == ""
        assert resolve(None) == ""
        assert resolve("invalid") == ""

    def test_empty_strings_array(self):
        """Test with empty strings array."""
        resolve = _get_string_resolver([])
        assert resolve(0) == ""


@pytest.mark.unit
class TestParseLayoutData:
    """Tests for _parse_layout_data function."""

    def test_parses_bounds_correctly(self):
        """Test parsing bounding boxes."""
        layout_data = {
            "nodeIndex": [1, 2],
            "bounds": [[10, 20, 100, 50], [5, 10, 200, 100]],
            "styles": [[], []],
        }
        resolve = _get_string_resolver([])

        layout_map = _parse_layout_data(layout_data, resolve)

        assert 1 in layout_map
        bounds1, _ = layout_map[1]
        assert bounds1 == BoundingBox(x=10, y=20, width=100, height=50)

        assert 2 in layout_map
        bounds2, _ = layout_map[2]
        assert bounds2 == BoundingBox(x=5, y=10, width=200, height=100)

    def test_parses_styles_correctly(self):
        """Test parsing computed styles."""
        layout_data = {
            "nodeIndex": [1],
            "bounds": [[0, 0, 100, 100]],
            "styles": [[0, 1, 2]],  # Indices for display, visibility, opacity
        }
        strings = ["block", "visible", "1"]
        resolve = _get_string_resolver(strings)

        layout_map = _parse_layout_data(layout_data, resolve)

        _, styles = layout_map[1]
        assert styles == {
            "display": "block",
            "visibility": "visible",
            "opacity": "1",
        }

    def test_handles_missing_bounds(self):
        """Test handles nodes without bounds."""
        layout_data = {
            "nodeIndex": [1],
            "bounds": [[1, 2]],  # Invalid bounds (less than 4 values)
            "styles": [[]],
        }
        resolve = _get_string_resolver([])

        layout_map = _parse_layout_data(layout_data, resolve)

        bounds, _ = layout_map[1]
        assert bounds is None

    def test_empty_layout_data(self):
        """Test with empty layout data."""
        layout_data = {
            "nodeIndex": [],
            "bounds": [],
            "styles": [],
        }
        resolve = _get_string_resolver([])

        layout_map = _parse_layout_data(layout_data, resolve)

        assert layout_map == {}


@pytest.mark.unit
class TestCreateElementNodes:
    """Tests for _create_element_nodes function."""

    def test_creates_element_nodes(self):
        """Test creating element nodes from CDP data."""
        nodes_data = {
            "nodeType": [1, 1],  # Two element nodes
            "nodeName": [0, 1],  # Indices to "div" and "button"
            "attributes": [[], []],
        }
        strings = ["div", "button"]
        layout_map = {}
        resolve = _get_string_resolver(strings)

        nodes = _create_element_nodes(nodes_data, layout_map, resolve)

        assert len(nodes) == 2
        assert nodes[0].tag == "div"
        assert nodes[1].tag == "button"

    def test_parses_attributes(self):
        """Test parsing element attributes."""
        nodes_data = {
            "nodeType": [1],
            "nodeName": [0],
            "attributes": [[1, 2, 3, 4]],  # id="test", class="btn"
        }
        strings = ["button", "id", "test", "class", "btn"]
        layout_map = {}
        resolve = _get_string_resolver(strings)

        nodes = _create_element_nodes(nodes_data, layout_map, resolve)

        assert nodes[0].attrib == {"id": "test", "class": "btn"}

    def test_includes_layout_data(self):
        """Test includes bounds and styles from layout_map."""
        nodes_data = {
            "nodeType": [1],
            "nodeName": [0],
            "attributes": [[]],
        }
        strings = ["div"]
        bounds = BoundingBox(10, 20, 100, 50)
        styles = {"display": "block"}
        layout_map = {0: (bounds, styles)}
        resolve = _get_string_resolver(strings)

        nodes = _create_element_nodes(nodes_data, layout_map, resolve)

        assert nodes[0].bounds == bounds
        assert nodes[0].styles == styles

    def test_skips_non_element_nodes(self):
        """Test skips non-element node types."""
        nodes_data = {
            "nodeType": [9, 1, 3],  # Document, Element, Text
            "nodeName": [-1, 0, -1],
            "attributes": [[], [], []],
        }
        strings = ["div"]
        layout_map = {}
        resolve = _get_string_resolver(strings)

        nodes = _create_element_nodes(nodes_data, layout_map, resolve)

        assert nodes[0] is None  # Document node
        assert nodes[1] is not None  # Element node
        assert nodes[2] is None  # Text node

    def test_stores_metadata(self):
        """Test stores CDP index in metadata."""
        nodes_data = {
            "nodeType": [1],
            "nodeName": [0],
            "attributes": [[]],
        }
        strings = ["div"]
        layout_map = {}
        resolve = _get_string_resolver(strings)

        nodes = _create_element_nodes(nodes_data, layout_map, resolve)

        assert nodes[0].metadata["cdp_index"] == 0
        assert nodes[0].backend_dom_node_id is None  # No backend_node_id provided


@pytest.mark.unit
class TestAddTextNodes:
    """Tests for _add_text_nodes function."""

    def test_adds_text_to_parent(self):
        """Test adds text nodes as children to parent elements."""
        # Create parent element
        parent = DomNode(tag="div", metadata={"cdp_index": 0})
        element_nodes = [parent]

        nodes_data = {
            "nodeType": [3],  # Text node
            "nodeValue": [0],  # Index to "Hello"
            "parentIndex": [0],  # Parent is element at index 0
        }
        strings = ["Hello"]
        resolve = _get_string_resolver(strings)

        _add_text_nodes(nodes_data, element_nodes, resolve)

        assert len(parent.children) == 1
        assert isinstance(parent.children[0], Text)
        assert parent.children[0].content == "Hello"

    def test_skips_empty_text(self):
        """Test skips text nodes with only whitespace."""
        parent = DomNode(tag="div", metadata={"cdp_index": 0})
        element_nodes = [parent]

        nodes_data = {
            "nodeType": [3, 3],
            "nodeValue": [0, 1],  # "   " and "Text"
            "parentIndex": [0, 0],
        }
        strings = ["   ", "Text"]
        resolve = _get_string_resolver(strings)

        _add_text_nodes(nodes_data, element_nodes, resolve)

        assert len(parent.children) == 1
        assert parent.children[0].content == "Text"

    def test_handles_missing_parent(self):
        """Test handles text nodes with invalid parent index."""
        element_nodes = [DomNode(tag="div")]

        nodes_data = {
            "nodeType": [3],
            "nodeValue": [0],
            "parentIndex": [10],  # Invalid parent index
        }
        strings = ["Text"]
        resolve = _get_string_resolver(strings)

        # Should not raise error
        _add_text_nodes(nodes_data, element_nodes, resolve)


@pytest.mark.unit
class TestBuildTree:
    """Tests for _build_tree function."""

    def test_builds_parent_child_relationships(self):
        """Test builds correct parent/child relationships."""
        # Create nodes: root, child1, child2
        root = DomNode(tag="div", metadata={"cdp_index": 0})
        child1 = DomNode(tag="span", metadata={"cdp_index": 1})
        child2 = DomNode(tag="button", metadata={"cdp_index": 2})
        element_nodes = [root, child1, child2]

        nodes_data = {
            "nodeType": [1, 1, 1],
            "parentIndex": [-1, 0, 0],  # root has no parent, children point to root
        }

        result = _build_tree(nodes_data, element_nodes)

        assert result == root
        assert len(root.children) == 2
        assert child1 in root.children
        assert child2 in root.children
        assert child1.parent == root
        assert child2.parent == root

    def test_builds_nested_structure(self):
        """Test builds nested tree structure."""
        # Create nodes: root > parent > child
        root = DomNode(tag="div", metadata={"cdp_index": 0})
        parent = DomNode(tag="section", metadata={"cdp_index": 1})
        child = DomNode(tag="span", metadata={"cdp_index": 2})
        element_nodes = [root, parent, child]

        nodes_data = {
            "nodeType": [1, 1, 1],
            "parentIndex": [-1, 0, 1],  # section -> div, span -> section
        }

        result = _build_tree(nodes_data, element_nodes)

        assert result == root
        assert parent in root.children
        assert child in parent.children
        assert child.parent == parent

    def test_returns_first_node_when_no_root(self):
        """Test returns first node when no explicit root found."""
        node1 = DomNode(tag="div", metadata={"cdp_index": 0})
        node2 = DomNode(tag="span", metadata={"cdp_index": 1})
        element_nodes = [None, node1, node2]  # No node at index 0

        nodes_data = {
            "nodeType": [1, 1, 1],
            "parentIndex": [10, 10, 10],  # All have invalid parent
        }

        result = _build_tree(nodes_data, element_nodes)

        assert result == node1


@pytest.mark.unit
class TestParseCdp:
    """Tests for parse_cdp function (end-to-end)."""

    def test_parses_complete_snapshot(self, sample_cdp_snapshot):
        """Test parsing complete CDP snapshot."""
        root = parse_cdp(sample_cdp_snapshot)

        assert root is not None
        assert root.tag == "html"
        assert len(root.children) == 2  # div and button

        # Check div
        div = root.children[0]
        assert div.tag == "div"
        assert div.attrib.get("id") == "container"
        assert len(div.children) == 1
        assert isinstance(div.children[0], Text)
        assert div.children[0].content == "Hello"

        # Check button
        button = root.children[1]
        assert button.tag == "button"
        assert len(button.children) == 1
        assert button.children[0].content == "Click"

    def test_parses_layout_information(self, sample_cdp_snapshot):
        """Test layout data is correctly attached to nodes."""
        root = parse_cdp(sample_cdp_snapshot)

        # Check html bounds
        assert root.bounds == BoundingBox(0, 0, 1024, 768)

        # Check div bounds
        div = root.children[0]
        assert div.bounds == BoundingBox(10, 10, 200, 50)

        # Check button bounds
        button = root.children[1]
        assert button.bounds == BoundingBox(10, 70, 100, 30)

    def test_parses_styles(self, sample_cdp_snapshot):
        """Test styles are correctly attached to nodes."""
        root = parse_cdp(sample_cdp_snapshot)

        assert root.styles == {
            "display": "block",
            "visibility": "visible",
            "opacity": "1",
        }

    def test_empty_snapshot_returns_default_node(self):
        """Test empty snapshot returns default html node."""
        empty_snapshot = {"documents": [], "strings": []}

        root = parse_cdp(empty_snapshot)

        assert root is not None
        assert root.tag == "html"
        assert root.metadata.get("cdp_index") == 0

    def test_preserves_metadata(self, sample_cdp_snapshot):
        """Test CDP metadata is preserved in nodes."""
        root = parse_cdp(sample_cdp_snapshot)

        # All nodes should have cdp_index
        for node in root.traverse():
            if isinstance(node, DomNode):
                assert "cdp_index" in node.metadata
                assert hasattr(node, "backend_dom_node_id")
