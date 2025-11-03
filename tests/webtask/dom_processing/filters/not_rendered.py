"""Tests for not rendered filter."""

import pytest
from webtask.dom_processing.filters.filter_not_rendered import filter_not_rendered
from webtask.dom.domnode import DomNode, Text, BoundingBox


@pytest.mark.unit
class TestFilterNotRendered:
    """Tests for filter_not_rendered function."""

    def test_removes_elements_without_styles_or_bounds(self):
        """Test removes elements with no layout data."""
        node = DomNode(
            tag="div",
            attrib={"id": "no-layout"},
            styles={},
            bounds=None,
        )

        result = filter_not_rendered(node)

        assert result is None

    def test_keeps_elements_with_styles(self):
        """Test keeps elements that have styles."""
        node = DomNode(
            tag="div",
            attrib={"id": "has-styles"},
            styles={"display": "block"},
            bounds=None,
        )

        result = filter_not_rendered(node)

        assert result is not None
        assert result.tag == "div"

    def test_keeps_elements_with_bounds(self):
        """Test keeps elements that have bounds."""
        node = DomNode(
            tag="div",
            attrib={"id": "has-bounds"},
            styles={},
            bounds=BoundingBox(10, 10, 100, 50),
        )

        result = filter_not_rendered(node)

        assert result is not None
        assert result.tag == "div"

    def test_keeps_elements_with_both(self):
        """Test keeps elements with both styles and bounds."""
        node = DomNode(
            tag="div",
            attrib={"id": "has-both"},
            styles={"display": "block"},
            bounds=BoundingBox(10, 10, 100, 50),
        )

        result = filter_not_rendered(node)

        assert result is not None
        assert result.tag == "div"

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(
            tag="div",
            styles={"display": "block"},
        )

        child_with_layout = DomNode(
            tag="span",
            attrib={"id": "with-layout"},
            styles={"color": "red"},
        )

        child_without_layout = DomNode(
            tag="span",
            attrib={"id": "without-layout"},
            styles={},
            bounds=None,
        )

        root.add_child(child_with_layout)
        root.add_child(child_without_layout)

        result = filter_not_rendered(root)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "with-layout"

    def test_preserves_text_children(self):
        """Test preserves text children."""
        node = DomNode(
            tag="p",
            styles={"display": "block"},
        )
        node.add_child(Text("Text content"))

        result = filter_not_rendered(node)

        assert result is not None
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Text content"

    def test_nested_filtering(self):
        """Test filters nested structures correctly."""
        # grandparent (has layout) > parent (no layout) > child (has layout)
        grandparent = DomNode(tag="div", styles={"display": "block"})
        parent = DomNode(tag="section", styles={}, bounds=None)
        child = DomNode(tag="span", styles={"color": "blue"})

        parent.add_child(child)
        grandparent.add_child(parent)

        result = filter_not_rendered(grandparent)

        # Parent should be removed, child should be gone too
        assert result is not None
        assert len(result.children) == 0

    def test_creates_new_node_copy(self):
        """Test creates a new node copy."""
        original = DomNode(
            tag="div",
            attrib={"id": "test"},
            styles={"display": "block"},
        )

        result = filter_not_rendered(original)

        assert result is not original
        assert result.tag == original.tag
        assert result.attrib == original.attrib
