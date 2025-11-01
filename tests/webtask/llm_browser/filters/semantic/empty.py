"""Tests for empty node filter."""

import pytest
from webtask.llm_browser.filters.semantic.empty import filter_empty
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterEmpty:
    """Tests for filter_empty function."""

    def test_removes_empty_non_interactive_elements(self):
        """Test removes empty elements that are not interactive."""
        empty_div = DomNode(tag="div", attrib={})

        result = filter_empty(empty_div)

        assert result is None

    def test_keeps_empty_interactive_elements(self):
        """Test keeps empty elements that are interactive."""
        empty_button = DomNode(tag="button", attrib={})

        result = filter_empty(empty_button)

        assert result is not None
        assert result.tag == "button"

    def test_keeps_elements_with_attributes(self):
        """Test keeps empty elements that have attributes."""
        div_with_attrib = DomNode(tag="div", attrib={"id": "test"})

        result = filter_empty(div_with_attrib)

        assert result is not None
        assert result.attrib["id"] == "test"

    def test_keeps_elements_with_non_empty_text(self):
        """Test keeps elements with non-empty text children."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Hello"))

        result = filter_empty(node)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].content == "Hello"

    def test_removes_whitespace_only_text(self):
        """Test removes text children with only whitespace."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("   \n\t  "))

        result = filter_empty(node)

        # Element is empty after removing whitespace text
        assert result is None

    def test_keeps_elements_with_element_children(self):
        """Test keeps elements that have element children."""
        parent = DomNode(tag="div", attrib={})
        child = DomNode(tag="span", attrib={"id": "child"})
        parent.add_child(child)

        result = filter_empty(parent)

        assert result is not None
        assert len(result.children) == 1

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(tag="div", attrib={"id": "root"})
        non_empty_child = DomNode(tag="span", attrib={"id": "child"})
        empty_child = DomNode(tag="div", attrib={})

        root.add_child(non_empty_child)
        root.add_child(empty_child)

        result = filter_empty(root)

        # Only non-empty child should remain
        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "child"

    def test_mixed_text_and_element_children(self):
        """Test handles mix of text and element children."""
        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Text "))
        node.add_child(DomNode(tag="span", attrib={"id": "s"}))
        node.add_child(Text(" more text"))

        result = filter_empty(node)

        assert result is not None
        assert len(result.children) == 3

    def test_nested_empty_removal(self):
        """Test removes nested empty elements."""
        # grandparent > empty_parent > empty_child
        grandparent = DomNode(tag="div", attrib={"id": "gp"})
        parent = DomNode(tag="section", attrib={})
        child = DomNode(tag="div", attrib={})

        parent.add_child(child)
        grandparent.add_child(parent)

        result = filter_empty(grandparent)

        # Both parent and child are empty, so grandparent has no children
        assert result is not None
        assert len(result.children) == 0

    def test_preserves_whitespace_in_non_empty_text(self):
        """Test preserves whitespace in text with actual content."""
        node = DomNode(tag="p", attrib={})
        node.add_child(Text("  Hello  World  "))

        result = filter_empty(node)

        assert result is not None
        assert result.children[0].content == "  Hello  World  "

    def test_empty_interactive_with_children(self):
        """Test interactive elements with children are kept."""
        button = DomNode(tag="button", attrib={})
        span = DomNode(tag="span", attrib={})
        button.add_child(span)

        result = filter_empty(button)

        # Button is kept even if it would be empty, but child span is removed
        assert result is not None
        # Span is not interactive and has no attributes/children, so it's removed
        assert len(result.children) == 0
