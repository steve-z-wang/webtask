"""Tests for non-visible tags filter."""

import pytest
from webtask.llm_browser.filters.visibility.non_visible_tags import (
    filter_non_visible_tags,
)
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterNonVisibleTags:
    """Tests for filter_non_visible_tags function."""

    def test_removes_tags_in_non_visible_set(self):
        """Test removes tags that are in the non-visible set."""
        non_visible_tags = {"script", "style", "meta"}

        script = DomNode(tag="script")
        style = DomNode(tag="style")
        meta = DomNode(tag="meta")

        assert filter_non_visible_tags(script, non_visible_tags) is None
        assert filter_non_visible_tags(style, non_visible_tags) is None
        assert filter_non_visible_tags(meta, non_visible_tags) is None

    def test_keeps_tags_not_in_set(self):
        """Test keeps tags that are not in the non-visible set."""
        non_visible_tags = {"script", "style"}

        div = DomNode(tag="div", attrib={"id": "content"})
        button = DomNode(tag="button")

        result_div = filter_non_visible_tags(div, non_visible_tags)
        result_button = filter_non_visible_tags(button, non_visible_tags)

        assert result_div is not None
        assert result_div.tag == "div"
        assert result_button is not None
        assert result_button.tag == "button"

    def test_empty_non_visible_set_keeps_all(self):
        """Test with empty non-visible set keeps all elements."""
        non_visible_tags = set()

        script = DomNode(tag="script")
        div = DomNode(tag="div")

        assert filter_non_visible_tags(script, non_visible_tags) is not None
        assert filter_non_visible_tags(div, non_visible_tags) is not None

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        non_visible_tags = {"script", "style"}

        root = DomNode(tag="div", attrib={"id": "root"})
        visible_child = DomNode(tag="p")
        hidden_child = DomNode(tag="script")

        root.add_child(visible_child)
        root.add_child(hidden_child)

        result = filter_non_visible_tags(root, non_visible_tags)

        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].tag == "p"

    def test_preserves_text_children(self):
        """Test preserves text children."""
        non_visible_tags = {"script"}

        node = DomNode(tag="div")
        node.add_child(Text("Hello"))

        result = filter_non_visible_tags(node, non_visible_tags)

        assert result is not None
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Hello"

    def test_nested_filtering(self):
        """Test filters nested non-visible tags."""
        non_visible_tags = {"script", "noscript"}

        # div > noscript > span
        root = DomNode(tag="div")
        noscript = DomNode(tag="noscript")
        span = DomNode(tag="span")

        noscript.add_child(span)
        root.add_child(noscript)

        result = filter_non_visible_tags(root, non_visible_tags)

        # noscript and its children should be removed
        assert result is not None
        assert len(result.children) == 0

    def test_mixed_visible_and_hidden(self):
        """Test correctly filters mix of visible and hidden elements."""
        non_visible_tags = {"script", "style", "meta", "link"}

        root = DomNode(tag="html")
        head = DomNode(tag="head")
        meta = DomNode(tag="meta")
        link = DomNode(tag="link")
        body = DomNode(tag="body")
        div = DomNode(tag="div")
        script = DomNode(tag="script")

        head.add_child(meta)
        head.add_child(link)
        body.add_child(div)
        body.add_child(script)
        root.add_child(head)
        root.add_child(body)

        result = filter_non_visible_tags(root, non_visible_tags)

        assert result is not None
        # head should have no children (meta and link removed)
        head_result = result.children[0]
        assert len(head_result.children) == 0
        # body should have only div (script removed)
        body_result = result.children[1]
        assert len(body_result.children) == 1
        assert body_result.children[0].tag == "div"

    def test_creates_new_node_copy(self):
        """Test creates a new node copy."""
        non_visible_tags = {"script"}

        original = DomNode(
            tag="div",
            attrib={"id": "test"},
        )

        result = filter_non_visible_tags(original, non_visible_tags)

        assert result is not original
        assert result.tag == original.tag
        assert result.attrib == original.attrib

    def test_case_sensitive_tag_matching(self):
        """Test tag matching is case-sensitive (tags should be lowercase)."""
        non_visible_tags = {"script"}

        # Lowercase tag - should be removed
        lowercase = DomNode(tag="script")
        # Uppercase tag - should NOT be removed (different tag)
        uppercase = DomNode(tag="SCRIPT")

        assert filter_non_visible_tags(lowercase, non_visible_tags) is None
        assert filter_non_visible_tags(uppercase, non_visible_tags) is not None
