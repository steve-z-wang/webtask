"""Tests for zero dimensions filter."""

import pytest
from webtask.llm_browser.filters.visibility.zero_dimensions import (
    filter_zero_dimensions,
)
from webtask.dom.domnode import DomNode, Text, BoundingBox


@pytest.mark.unit
class TestFilterZeroDimensions:
    """Tests for filter_zero_dimensions function."""

    def test_removes_zero_width_without_visible_children(self):
        """Test removes elements with zero width and no visible children."""
        node = DomNode(
            tag="div",
            attrib={"id": "zero-width"},
            bounds=BoundingBox(10, 10, 0, 50),  # width=0
        )

        result = filter_zero_dimensions(node)

        assert result is None

    def test_removes_zero_height_without_visible_children(self):
        """Test removes elements with zero height and no visible children."""
        node = DomNode(
            tag="div",
            attrib={"id": "zero-height"},
            bounds=BoundingBox(10, 10, 100, 0),  # height=0
        )

        result = filter_zero_dimensions(node)

        assert result is None

    def test_removes_both_zero(self):
        """Test removes elements with both zero width and height."""
        node = DomNode(
            tag="div",
            bounds=BoundingBox(0, 0, 0, 0),
        )

        result = filter_zero_dimensions(node)

        assert result is None

    def test_keeps_normal_sized_elements(self):
        """Test keeps elements with non-zero dimensions."""
        node = DomNode(
            tag="div",
            attrib={"id": "normal"},
            bounds=BoundingBox(10, 10, 100, 50),
        )

        result = filter_zero_dimensions(node)

        assert result is not None
        assert result.attrib["id"] == "normal"

    def test_keeps_zero_size_with_visible_children(self):
        """Test keeps zero-size elements if they have visible (non-zero) children."""
        parent = DomNode(
            tag="div",
            attrib={"id": "parent"},
            bounds=BoundingBox(0, 0, 0, 0),  # Zero size
        )

        child = DomNode(
            tag="span",
            attrib={"id": "child"},
            bounds=BoundingBox(10, 10, 100, 50),  # Non-zero size
        )

        parent.add_child(child)

        result = filter_zero_dimensions(parent)

        # Parent should be kept because it has a visible child
        assert result is not None
        assert result.attrib["id"] == "parent"
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "child"

    def test_keeps_elements_without_bounds(self):
        """Test keeps elements that have no bounds data."""
        node = DomNode(
            tag="div",
            attrib={"id": "no-bounds"},
            bounds=None,
        )

        result = filter_zero_dimensions(node)

        assert result is not None
        assert result.attrib["id"] == "no-bounds"

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(
            tag="div",
            attrib={"id": "root"},
            bounds=BoundingBox(0, 0, 100, 100),
        )

        visible_child = DomNode(
            tag="span",
            attrib={"id": "visible"},
            bounds=BoundingBox(10, 10, 50, 50),
        )

        zero_child = DomNode(
            tag="span",
            attrib={"id": "zero"},
            bounds=BoundingBox(0, 0, 0, 0),
        )

        root.add_child(visible_child)
        root.add_child(zero_child)

        result = filter_zero_dimensions(root)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "visible"

    def test_preserves_text_children(self):
        """Test preserves text children."""
        node = DomNode(
            tag="p",
            bounds=BoundingBox(10, 10, 100, 50),
        )
        node.add_child(Text("Text content"))

        result = filter_zero_dimensions(node)

        assert result is not None
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Text content"

    def test_text_children_dont_count_as_visible(self):
        """Test text children don't count as visible children for zero-size parents."""
        parent = DomNode(
            tag="div",
            bounds=BoundingBox(0, 0, 0, 0),
        )
        parent.add_child(Text("Just text"))

        result = filter_zero_dimensions(parent)

        # Should be removed because text nodes don't count as "visible children"
        assert result is None

    def test_nested_zero_dimension_filtering(self):
        """Test correctly filters nested zero-dimension elements."""
        # grandparent (normal) > parent (zero, no visible children) > child (zero)
        grandparent = DomNode(
            tag="div",
            bounds=BoundingBox(0, 0, 200, 200),
        )

        parent = DomNode(
            tag="section",
            bounds=BoundingBox(0, 0, 0, 0),
        )

        child = DomNode(
            tag="span",
            bounds=BoundingBox(0, 0, 0, 0),
        )

        parent.add_child(child)
        grandparent.add_child(parent)

        result = filter_zero_dimensions(grandparent)

        # Parent and child should both be removed
        assert result is not None
        assert len(result.children) == 0

    def test_creates_new_node_copy(self):
        """Test creates a new node copy."""
        original = DomNode(
            tag="div",
            attrib={"id": "test"},
            bounds=BoundingBox(10, 10, 100, 50),
        )

        result = filter_zero_dimensions(original)

        assert result is not original
        assert result.tag == original.tag
        assert result.attrib == original.attrib

    def test_mixed_zero_and_normal_children(self):
        """Test filters mix of zero and normal-sized children correctly."""
        root = DomNode(
            tag="div",
            bounds=BoundingBox(0, 0, 200, 200),
        )

        for i in range(5):
            child = DomNode(
                tag="span",
                attrib={"id": f"child-{i}"},
                bounds=BoundingBox(
                    0, 0, 0 if i % 2 == 0 else 50, 50
                ),  # Even indices have zero width
            )
            root.add_child(child)

        result = filter_zero_dimensions(root)

        # Only odd-indexed children should remain (1, 3)
        assert result is not None
        assert len(result.children) == 2
        assert result.children[0].attrib["id"] == "child-1"
        assert result.children[1].attrib["id"] == "child-3"
