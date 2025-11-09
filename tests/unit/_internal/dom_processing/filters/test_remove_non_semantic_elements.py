"""Tests for _remove_non_semantic_elements filter."""

import pytest
from webtask._internal.dom_processing.filters.filter_non_semantic import (
    _remove_non_semantic_elements,
)
from webtask._internal.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestRemoveNonSemanticElements:
    """Tests for remove_non_semantic_elements function."""

    def test_removes_empty_non_interactive_elements(self):
        """Test removes empty elements that are not interactive."""
        empty_div = DomNode(tag="div", attrib={})

        result = _remove_non_semantic_elements(empty_div)

        assert result is None

    def test_keeps_empty_interactive_elements(self):
        """Test keeps empty elements that are interactive."""
        empty_button = DomNode(tag="button", attrib={})

        result = _remove_non_semantic_elements(empty_button)

        assert result is not None
        assert result.tag == "button"

    def test_keeps_elements_with_attributes(self):
        """Test keeps empty elements that have semantic attributes."""
        div_with_attrib = DomNode(tag="div", attrib={"role": "region"})

        result = _remove_non_semantic_elements(div_with_attrib)

        assert result is not None
        assert result.attrib["role"] == "region"

    def test_keeps_elements_with_non_empty_text(self):
        """Test keeps elements with non-empty text children."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Hello"))

        result = _remove_non_semantic_elements(node)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].content == "Hello"

    def test_removes_whitespace_only_text(self):
        """Test removes text children with only whitespace."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("   \n\t  "))

        result = _remove_non_semantic_elements(node)

        # Element is empty after removing whitespace text
        assert result is None

    def test_keeps_elements_with_element_children(self):
        """Test keeps elements that have element children."""
        parent = DomNode(tag="div", attrib={})
        child = DomNode(tag="span", attrib={"role": "button"})
        parent.add_child(child)

        result = _remove_non_semantic_elements(parent)

        assert result is not None
        assert len(result.children) == 1

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(tag="div", attrib={"role": "main"})
        non_empty_child = DomNode(tag="span", attrib={"role": "status"})
        empty_child = DomNode(tag="div", attrib={})

        root.add_child(non_empty_child)
        root.add_child(empty_child)

        result = _remove_non_semantic_elements(root)

        # Only non-empty child should remain
        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["role"] == "status"

    def test_mixed_text_and_element_children(self):
        """Test handles mix of text and element children."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Text "))
        node.add_child(DomNode(tag="span", attrib={"role": "alert"}))
        node.add_child(Text(" more text"))

        result = _remove_non_semantic_elements(node)

        assert result is not None
        assert len(result.children) == 3

    def test_nested_empty_removal(self):
        """Test removes nested empty elements."""
        # grandparent > empty_parent > empty_child
        grandparent = DomNode(tag="div", attrib={"role": "banner"})
        parent = DomNode(tag="section", attrib={})
        child = DomNode(tag="div", attrib={})

        parent.add_child(child)
        grandparent.add_child(parent)

        result = _remove_non_semantic_elements(grandparent)

        # Both parent and child are empty, so grandparent has no children
        assert result is not None
        assert len(result.children) == 0

    def test_preserves_whitespace_in_non_empty_text(self):
        """Test preserves whitespace in text with actual content."""
        node = DomNode(tag="p", attrib={})
        node.add_child(Text("  Hello  World  "))

        result = _remove_non_semantic_elements(node)

        assert result is not None
        assert result.children[0].content == "  Hello  World  "

    def test_empty_interactive_with_children(self):
        """Test interactive elements with children are kept."""
        button = DomNode(tag="button", attrib={})
        span = DomNode(tag="span", attrib={})
        button.add_child(span)

        result = _remove_non_semantic_elements(button)

        # Button is kept even if it would be empty, but child span is removed
        assert result is not None
        # Span is not interactive and has no attributes/children, so it's removed
        assert len(result.children) == 0
