"""Tests for CSS hidden filter."""

import pytest
from webtask.llm_browser.filters.visibility.css_hidden import filter_css_hidden
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterCssHidden:
    """Tests for filter_css_hidden function."""

    def test_removes_display_none(self):
        """Test removes elements with display:none."""
        node = DomNode(
            tag="div",
            attrib={"id": "hidden"},
            styles={"display": "none"},
        )

        result = filter_css_hidden(node)

        assert result is None

    def test_removes_visibility_hidden(self):
        """Test removes elements with visibility:hidden."""
        node = DomNode(
            tag="div",
            attrib={"id": "hidden"},
            styles={"visibility": "hidden"},
        )

        result = filter_css_hidden(node)

        assert result is None

    def test_removes_opacity_zero(self):
        """Test removes elements with opacity:0."""
        node = DomNode(
            tag="div",
            attrib={"id": "hidden"},
            styles={"opacity": "0"},
        )

        result = filter_css_hidden(node)

        assert result is None

    def test_removes_hidden_attribute(self):
        """Test removes elements with hidden attribute."""
        node = DomNode(
            tag="div",
            attrib={"hidden": ""},
            styles={},
        )

        result = filter_css_hidden(node)

        assert result is None

    def test_removes_hidden_input(self):
        """Test removes input elements with type=hidden."""
        node = DomNode(
            tag="input",
            attrib={"type": "hidden", "name": "csrf_token"},
            styles={},
        )

        result = filter_css_hidden(node)

        assert result is None

    def test_keeps_visible_elements(self, visible_element):
        """Test keeps visible elements."""
        result = filter_css_hidden(visible_element)

        assert result is not None
        assert result.tag == "div"
        assert result.attrib["id"] == "visible"

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(
            tag="div",
            attrib={"id": "root"},
            styles={"display": "block"},
        )

        visible_child = DomNode(
            tag="span",
            attrib={"id": "visible"},
            styles={"display": "inline"},
        )

        hidden_child = DomNode(
            tag="span",
            attrib={"id": "hidden"},
            styles={"display": "none"},
        )

        root.add_child(visible_child)
        root.add_child(hidden_child)

        result = filter_css_hidden(root)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].attrib["id"] == "visible"

    def test_preserves_text_children(self):
        """Test preserves text children."""
        node = DomNode(
            tag="p",
            attrib={},
            styles={"display": "block"},
        )
        node.add_child(Text("Hello world"))

        result = filter_css_hidden(node)

        assert result is not None
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Hello world"

    def test_handles_invalid_opacity(self):
        """Test handles invalid opacity values gracefully."""
        node = DomNode(
            tag="div",
            attrib={},
            styles={"opacity": "invalid"},
        )

        result = filter_css_hidden(node)

        # Should not crash, should keep the element
        assert result is not None

    def test_case_insensitive_matching(self):
        """Test CSS values are matched case-insensitively."""
        node1 = DomNode(tag="div", styles={"display": "NONE"})
        node2 = DomNode(tag="div", styles={"visibility": "HIDDEN"})
        node3 = DomNode(tag="input", attrib={"type": "HIDDEN"})

        assert filter_css_hidden(node1) is None
        assert filter_css_hidden(node2) is None
        assert filter_css_hidden(node3) is None

    def test_creates_new_node_copy(self):
        """Test creates a new node copy, not modifying original."""
        original = DomNode(
            tag="div",
            attrib={"id": "test"},
            styles={"display": "block"},
            metadata={"cdp_index": 0},
        )
        child = DomNode(tag="span")
        original.add_child(child)

        result = filter_css_hidden(original)

        assert result is not original
        assert result.tag == original.tag
        assert result.attrib == original.attrib
        # Original should be unchanged
        assert len(original.children) == 1
