"""Tests for attribute filter."""

import pytest
from webtask.llm_browser.filters.semantic.attributes import filter_attributes
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterAttributes:
    """Tests for filter_attributes function."""

    def test_keeps_attributes_in_keep_set(self):
        """Test keeps attributes that are in the keep set."""
        keep = {"id", "role", "aria-label"}

        node = DomNode(
            tag="button",
            attrib={
                "id": "submit-btn",
                "role": "button",
                "aria-label": "Submit form",
                "class": "btn-primary",  # Not in keep set
                "data-test": "submit",  # Not in keep set
            },
        )

        result = filter_attributes(node, keep)

        assert result.attrib == {
            "id": "submit-btn",
            "role": "button",
            "aria-label": "Submit form",
        }
        # class and data-test should be removed
        assert "class" not in result.attrib
        assert "data-test" not in result.attrib

    def test_removes_all_attributes_when_none_in_keep_set(self):
        """Test removes all attributes when none are in keep set."""
        keep = {"id", "role"}

        node = DomNode(
            tag="div",
            attrib={
                "class": "container",
                "style": "color: red",
                "data-id": "123",
            },
        )

        result = filter_attributes(node, keep)

        assert result.attrib == {}

    def test_keeps_all_attributes_when_all_in_keep_set(self):
        """Test keeps all attributes when all are in keep set."""
        keep = {"id", "class", "style"}

        node = DomNode(
            tag="div",
            attrib={
                "id": "main",
                "class": "container",
                "style": "width: 100%",
            },
        )

        result = filter_attributes(node, keep)

        assert result.attrib == {
            "id": "main",
            "class": "container",
            "style": "width: 100%",
        }

    def test_empty_keep_set_removes_all(self):
        """Test empty keep set removes all attributes."""
        keep = set()

        node = DomNode(
            tag="div",
            attrib={"id": "test", "class": "foo"},
        )

        result = filter_attributes(node, keep)

        assert result.attrib == {}

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        keep = {"id"}

        root = DomNode(
            tag="div",
            attrib={"id": "root", "class": "container"},
        )

        child = DomNode(
            tag="span",
            attrib={"id": "child", "data-test": "value"},
        )

        root.add_child(child)

        result = filter_attributes(root, keep)

        assert result.attrib == {"id": "root"}
        assert len(result.children) == 1
        assert result.children[0].attrib == {"id": "child"}

    def test_preserves_text_children(self):
        """Test preserves text children."""
        keep = {"id"}

        node = DomNode(
            tag="p",
            attrib={"id": "paragraph", "class": "text"},
        )
        node.add_child(Text("Hello world"))

        result = filter_attributes(node, keep)

        assert result.attrib == {"id": "paragraph"}
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Hello world"

    def test_preserves_node_properties_except_attrib(self):
        """Test preserves all node properties except attributes."""
        from webtask.dom.domnode import BoundingBox

        keep = {"id"}

        node = DomNode(
            tag="div",
            attrib={"id": "test", "class": "foo", "data-x": "y"},
            styles={"display": "block", "color": "red"},
            bounds=BoundingBox(10, 10, 100, 50),
            metadata={"cdp_index": 42},
        )

        result = filter_attributes(node, keep)

        # Attributes filtered
        assert result.attrib == {"id": "test"}
        # Other properties preserved
        assert result.tag == "div"
        assert result.styles == {"display": "block", "color": "red"}
        assert result.bounds == BoundingBox(10, 10, 100, 50)
        assert result.metadata == {"cdp_index": 42}

    def test_nested_filtering(self):
        """Test filters nested structures correctly."""
        keep = {"id", "type"}

        # grandparent > parent > child
        grandparent = DomNode(
            tag="form",
            attrib={"id": "form", "class": "form-class", "method": "post"},
        )

        parent = DomNode(
            tag="fieldset",
            attrib={"id": "fields", "data-group": "1"},
        )

        child = DomNode(
            tag="input",
            attrib={"id": "name", "type": "text", "placeholder": "Enter name"},
        )

        parent.add_child(child)
        grandparent.add_child(parent)

        result = filter_attributes(grandparent, keep)

        # Check all levels
        assert result.attrib == {"id": "form"}
        assert result.children[0].attrib == {"id": "fields"}
        assert result.children[0].children[0].attrib == {"id": "name", "type": "text"}

    def test_creates_new_node_not_modifying_original(self):
        """Test creates new node without modifying original."""
        keep = {"id"}

        original = DomNode(
            tag="div",
            attrib={"id": "test", "class": "foo", "data-x": "y"},
        )

        result = filter_attributes(original, keep)

        # Result should have filtered attributes
        assert result.attrib == {"id": "test"}
        # Original should be unchanged
        assert original.attrib == {"id": "test", "class": "foo", "data-x": "y"}
        # Should be different objects
        assert result is not original

    def test_case_sensitive_matching(self):
        """Test attribute names are matched case-sensitively."""
        keep = {"id", "data-ID"}  # Note: data-ID with uppercase

        node = DomNode(
            tag="div",
            attrib={
                "id": "test",
                "ID": "TEST",  # Different case
                "data-id": "lower",
                "data-ID": "mixed",
            },
        )

        result = filter_attributes(node, keep)

        # Only exact matches should be kept
        assert result.attrib == {"id": "test", "data-ID": "mixed"}
        assert "ID" not in result.attrib
        assert "data-id" not in result.attrib
