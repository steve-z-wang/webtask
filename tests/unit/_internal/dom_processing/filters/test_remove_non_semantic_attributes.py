"""Tests for attribute filter."""

import pytest
from webtask._internal.cdp.dom.filters.filter_non_semantic import (
    _remove_non_semantic_attributes,
)
from webtask._internal.cdp.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestRemoveNonSemanticAttributes:
    """Tests for remove_non_semantic_attributes function."""

    def test_keeps_semantic_attributes(self):
        """Test keeps semantic attributes like role, aria-label, type."""
        node = DomNode(
            tag="button",
            attrib={
                "role": "button",
                "aria-label": "Submit form",
                "type": "submit",
                "class": "btn-primary",  # Not semantic
                "data-test": "submit",  # Not semantic
                "id": "submit-btn",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        # Semantic attributes should be kept
        assert result.attrib == {
            "role": "button",
            "aria-label": "Submit form",
            "type": "submit",
        }
        # Non-semantic attributes should be removed
        assert "class" not in result.attrib
        assert "data-test" not in result.attrib
        assert "id" not in result.attrib

    def test_removes_non_semantic_attributes(self):
        """Test removes all non-semantic attributes."""
        node = DomNode(
            tag="div",
            attrib={
                "class": "container",
                "style": "color: red",
                "data-id": "123",
                "id": "main",
            },
        )

        result = _remove_non_semantic_attributes(node)

        # All attributes should be removed (none are semantic)
        assert result.attrib == {}

    def test_keeps_form_element_attributes(self):
        """Test keeps semantic form/input attributes."""
        node = DomNode(
            tag="input",
            attrib={
                "type": "text",
                "name": "username",
                "placeholder": "Enter username",
                "value": "john",
                "disabled": "true",
                "class": "form-control",  # Not semantic
                "id": "username-input",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {
            "type": "text",
            "name": "username",
            "placeholder": "Enter username",
            "value": "john",
            "disabled": "true",
        }
        assert "class" not in result.attrib
        assert "id" not in result.attrib

    def test_keeps_aria_attributes(self):
        """Test keeps ARIA attributes."""
        node = DomNode(
            tag="div",
            attrib={
                "aria-checked": "true",
                "aria-selected": "false",
                "aria-expanded": "true",
                "aria-hidden": "false",
                "aria-disabled": "true",
                "aria-haspopup": "menu",
                "class": "menu-item",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {
            "aria-checked": "true",
            "aria-selected": "false",
            "aria-expanded": "true",
            "aria-hidden": "false",
            "aria-disabled": "true",
            "aria-haspopup": "menu",
        }
        assert "class" not in result.attrib

    def test_keeps_interaction_attributes(self):
        """Test keeps interaction attributes like tabindex and onclick."""
        node = DomNode(
            tag="div",
            attrib={
                "tabindex": "0",
                "onclick": "handleClick()",
                "data-action": "delete",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {
            "tabindex": "0",
            "onclick": "handleClick()",
        }
        assert "data-action" not in result.attrib

    def test_keeps_file_input_accept_attribute(self):
        """Test keeps accept attribute for file inputs."""
        node = DomNode(
            tag="input",
            attrib={
                "type": "file",
                "accept": "image/*",
                "id": "file-upload",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {
            "type": "file",
            "accept": "image/*",
        }
        assert "id" not in result.attrib

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(
            tag="div",
            attrib={"role": "navigation", "class": "container"},
        )

        child = DomNode(
            tag="button",
            attrib={"type": "button", "data-test": "value"},
        )

        root.add_child(child)

        result = _remove_non_semantic_attributes(root)

        assert result.attrib == {"role": "navigation"}
        assert len(result.children) == 1
        assert result.children[0].attrib == {"type": "button"}

    def test_preserves_text_children(self):
        """Test preserves text children."""
        node = DomNode(
            tag="p",
            attrib={"role": "text", "class": "text"},
        )
        node.add_child(Text("Hello world"))

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {"role": "text"}
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Hello world"

    def test_preserves_node_properties_except_attrib(self):
        """Test preserves all node properties except attributes."""
        from webtask._internal.cdp.dom.domnode import BoundingBox

        node = DomNode(
            tag="div",
            attrib={"role": "button", "class": "foo", "data-x": "y"},
            styles={"display": "block", "color": "red"},
            bounds=BoundingBox(10, 10, 100, 50),
            metadata={"cdp_index": 42},
        )

        result = _remove_non_semantic_attributes(node)

        # Attributes filtered
        assert result.attrib == {"role": "button"}
        # Other properties preserved
        assert result.tag == "div"
        assert result.styles == {"display": "block", "color": "red"}
        assert result.bounds == BoundingBox(10, 10, 100, 50)
        assert result.metadata == {"cdp_index": 42}

    def test_nested_filtering(self):
        """Test filters nested structures correctly."""
        # grandparent > parent > child
        grandparent = DomNode(
            tag="form",
            attrib={"role": "form", "class": "form-class", "method": "post"},
        )

        parent = DomNode(
            tag="fieldset",
            attrib={"role": "group", "data-group": "1"},
        )

        child = DomNode(
            tag="input",
            attrib={"type": "text", "name": "username", "placeholder": "Enter name"},
        )

        parent.add_child(child)
        grandparent.add_child(parent)

        result = _remove_non_semantic_attributes(grandparent)

        # Check all levels
        assert result.attrib == {"role": "form"}
        assert result.children[0].attrib == {"role": "group"}
        assert result.children[0].children[0].attrib == {
            "type": "text",
            "name": "username",
            "placeholder": "Enter name",
        }

    def test_creates_new_node_not_modifying_original(self):
        """Test creates new node without modifying original."""
        original = DomNode(
            tag="div",
            attrib={"role": "button", "class": "foo", "data-x": "y"},
        )

        result = _remove_non_semantic_attributes(original)

        # Result should have filtered attributes
        assert result.attrib == {"role": "button"}
        # Original should be unchanged
        assert original.attrib == {"role": "button", "class": "foo", "data-x": "y"}
        # Should be different objects
        assert result is not original

    def test_empty_attrib_remains_empty(self):
        """Test node with no attributes remains empty."""
        node = DomNode(tag="div", attrib={})

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {}

    def test_keeps_alt_and_title_attributes(self):
        """Test keeps alt and title attributes."""
        node = DomNode(
            tag="img",
            attrib={
                "alt": "Profile picture",
                "title": "John Doe",
                "src": "image.jpg",  # Not semantic
                "class": "avatar",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(node)

        assert result.attrib == {
            "alt": "Profile picture",
            "title": "John Doe",
        }
        assert "src" not in result.attrib
        assert "class" not in result.attrib

    def test_keeps_checked_and_selected_attributes(self):
        """Test keeps checked and selected state attributes."""
        checkbox = DomNode(
            tag="input",
            attrib={
                "type": "checkbox",
                "checked": "true",
                "id": "agree",  # Not semantic
            },
        )

        result = _remove_non_semantic_attributes(checkbox)

        assert result.attrib == {
            "type": "checkbox",
            "checked": "true",
        }
        assert "id" not in result.attrib
