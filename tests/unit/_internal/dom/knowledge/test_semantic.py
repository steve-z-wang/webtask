"""Tests for semantic knowledge functions."""

import pytest

from webtask._internal.dom.domnode import DomNode, Text
from webtask._internal.dom.knowledge.semantic import has_semantic_value, SEMANTIC_TAGS


@pytest.mark.unit
class TestSemanticTags:
    """Test that semantic HTML tags are preserved."""

    def test_li_has_semantic_value(self):
        """li elements should have semantic value (for dropdown menus, lists)."""
        node = DomNode(tag="li")
        assert has_semantic_value(node) is True

    def test_ul_has_semantic_value(self):
        """ul elements should have semantic value."""
        node = DomNode(tag="ul")
        assert has_semantic_value(node) is True

    def test_ol_has_semantic_value(self):
        """ol elements should have semantic value."""
        node = DomNode(tag="ol")
        assert has_semantic_value(node) is True

    def test_semantic_tags_constant(self):
        """Verify SEMANTIC_TAGS contains expected tags."""
        assert "li" in SEMANTIC_TAGS
        assert "ul" in SEMANTIC_TAGS
        assert "ol" in SEMANTIC_TAGS


@pytest.mark.unit
class TestHasSemanticValue:
    """Test has_semantic_value function."""

    def test_text_node_with_content(self):
        """Text nodes with content have semantic value."""
        node = Text(content="Hello")
        assert has_semantic_value(node) is True

    def test_text_node_empty(self):
        """Empty text nodes don't have semantic value."""
        node = Text(content="   ")
        assert has_semantic_value(node) is False

    def test_script_tag_filtered(self):
        """Script tags are filtered out."""
        node = DomNode(tag="script")
        assert has_semantic_value(node) is False

    def test_style_tag_filtered(self):
        """Style tags are filtered out."""
        node = DomNode(tag="style")
        assert has_semantic_value(node) is False

    def test_div_without_attributes(self):
        """Plain div without attributes has no semantic value."""
        node = DomNode(tag="div")
        assert has_semantic_value(node) is False

    def test_div_with_aria_label(self):
        """Div with aria-label has semantic value."""
        node = DomNode(tag="div", attrib={"aria-label": "Menu"})
        assert has_semantic_value(node) is True

    def test_div_with_role(self):
        """Div with role attribute has semantic value."""
        node = DomNode(tag="div", attrib={"role": "button"})
        assert has_semantic_value(node) is True

    def test_div_with_tabindex(self):
        """Div with tabindex is interactive, has semantic value."""
        node = DomNode(tag="div", attrib={"tabindex": "0"})
        assert has_semantic_value(node) is True

    def test_presentation_role_filtered(self):
        """Elements with role=presentation are filtered."""
        node = DomNode(tag="div", attrib={"role": "presentation"})
        assert has_semantic_value(node) is False

    def test_none_role_filtered(self):
        """Elements with role=none are filtered."""
        node = DomNode(tag="div", attrib={"role": "none"})
        assert has_semantic_value(node) is False

    def test_interactive_button(self):
        """Button elements are interactive, have semantic value."""
        node = DomNode(tag="button")
        assert has_semantic_value(node) is True

    def test_interactive_input(self):
        """Input elements are interactive, have semantic value."""
        node = DomNode(tag="input")
        assert has_semantic_value(node) is True

    def test_interactive_anchor(self):
        """Anchor elements are interactive, have semantic value."""
        node = DomNode(tag="a")
        assert has_semantic_value(node) is True
