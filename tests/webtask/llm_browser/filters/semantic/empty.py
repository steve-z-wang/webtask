"""Tests for empty node filter."""

import pytest
from webtask.llm_browser.filters.semantic.empty import filter_empty
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterEmpty:
    """Tests for filter_empty function."""

    def test_removes_empty_non_interactive_elements(self):
        """Test removes empty elements that are not interactive."""
        interactive_tags = {"button", "input", "a"}

        empty_div = DomNode(tag="div", attrib={})

        result = filter_empty(empty_div, interactive_tags)

        assert result is None

    def test_keeps_empty_interactive_elements(self):
        """Test keeps empty elements that are interactive."""
        interactive_tags = {"button", "input", "a"}

        empty_button = DomNode(tag="button", attrib={})

        result = filter_empty(empty_button, interactive_tags)

        assert result is not None
        assert result.tag == "button"

    def test_keeps_elements_with_attributes(self):
        """Test keeps empty elements that have attributes."""
        interactive_tags = {"button"}

        div_with_attrib = DomNode(tag="div", attrib={"id": "test"})

        result = filter_empty(div_with_attrib, interactive_tags)

        assert result is not None
        assert result.attrib["id"] == "test"

    def test_keeps_elements_with_non_empty_text(self):
        """Test keeps elements with non-empty text children."""
        interactive_tags = {"button"}

        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Hello"))

        result = filter_empty(node, interactive_tags)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].content == "Hello"

    def test_removes_whitespace_only_text(self):
        """Test removes text children with only whitespace."""
        interactive_tags = {"button"}

        node = DomNode(tag="div", attrib={})
        node.add_child(Text("   \n\t  "))

        result = filter_empty(node, interactive_tags)

        # Element is empty after removing whitespace text
        assert result is None

    def test_keeps_elements_with_element_children(self):
        """Test keeps elements that have element children."""
        interactive_tags = {"button"}

        parent = DomNode(tag="div", attrib={})
        child = DomNode(tag="span", attrib={"id": "child"})
        parent.add_child(child)

        result = filter_empty(parent, interactive_tags)

        assert result is not None
        assert len(result.children) == 1

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        interactive_tags = {"button"}

        root = DomNode(tag="div", attrib={"id": "root"})
        non_empty_child = DomNode(tag="span", attrib={"id": "child"})
        empty_child = DomNode(tag="div", attrib={})

        root.add_child(non_empty_child)
        root.add_child(empty_child)

        result = filter_empty(root, interactive_tags)

        # Only non-empty child should remain
        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "child"

    def test_mixed_text_and_element_children(self):
        """Test handles mix of text and element children."""
        interactive_tags = {"button"}

        node = DomNode(tag="div", attrib={})
        node.add_child(Text("Text "))
        node.add_child(DomNode(tag="span", attrib={"id": "s"}))
        node.add_child(Text(" more text"))

        result = filter_empty(node, interactive_tags)

        assert result is not None
        assert len(result.children) == 3

    def test_nested_empty_removal(self):
        """Test removes nested empty elements."""
        interactive_tags = {"button"}

        # grandparent > empty_parent > empty_child
        grandparent = DomNode(tag="div", attrib={"id": "gp"})
        parent = DomNode(tag="section", attrib={})
        child = DomNode(tag="div", attrib={})

        parent.add_child(child)
        grandparent.add_child(parent)

        result = filter_empty(grandparent, interactive_tags)

        # Both parent and child are empty, so grandparent has no children
        assert result is not None
        assert len(result.children) == 0

    def test_preserves_whitespace_in_non_empty_text(self):
        """Test preserves whitespace in text with actual content."""
        interactive_tags = {"button"}

        node = DomNode(tag="p", attrib={})
        node.add_child(Text("  Hello  World  "))

        result = filter_empty(node, interactive_tags)

        assert result is not None
        assert result.children[0].content == "  Hello  World  "

    def test_empty_interactive_with_children(self):
        """Test interactive elements with children are kept."""
        interactive_tags = {"button"}

        button = DomNode(tag="button", attrib={})
        span = DomNode(tag="span", attrib={})
        button.add_child(span)

        result = filter_empty(button, interactive_tags)

        # Button is kept even if it would be empty, but child span is removed
        assert result is not None
        # Span is not interactive and has no attributes/children, so it's removed
        assert len(result.children) == 0
