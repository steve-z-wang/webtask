"""Tests for wrapper collapse filter."""

import pytest
from webtask.dom_processing.filters.filter_non_semantic import (
    _collapse_non_semantic_wrappers,
)
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestCollapseNonSemanticWrappers:
    """Tests for collapse_non_semantic_wrappers function."""

    def test_collapses_wrapper_with_single_element_child(self):
        """Test collapses wrapper element with single element child."""
        wrapper = DomNode(tag="div", attrib={})  # No attributes
        child = DomNode(tag="span", attrib={"id": "child"})
        wrapper.add_child(child)

        result = _collapse_non_semantic_wrappers(wrapper)

        # Wrapper should be collapsed, returning child directly
        assert result is child or (
            result.tag == "span" and result.attrib == {"id": "child"}
        )

    def test_keeps_wrapper_with_attributes(self):
        """Test keeps wrapper that has semantic attributes."""
        wrapper = DomNode(tag="div", attrib={"role": "navigation"})
        child = DomNode(tag="span", attrib={"role": "button"})
        wrapper.add_child(child)

        result = _collapse_non_semantic_wrappers(wrapper)

        # Wrapper has semantic attributes, so it should not be collapsed
        assert result.tag == "div"
        assert result.attrib == {"role": "navigation"}
        assert len(result.children) == 1

    def test_keeps_wrapper_with_multiple_element_children(self):
        """Test keeps wrapper with multiple element children."""
        wrapper = DomNode(tag="div", attrib={})
        child1 = DomNode(tag="span", attrib={"id": "c1"})
        child2 = DomNode(tag="span", attrib={"id": "c2"})

        wrapper.add_child(child1)
        wrapper.add_child(child2)

        result = _collapse_non_semantic_wrappers(wrapper)

        # Wrapper has 2 children, so it should not be collapsed
        assert result.tag == "div"
        assert len(result.children) == 2

    def test_keeps_wrapper_with_meaningful_text(self):
        """Test keeps wrapper that has meaningful text."""
        wrapper = DomNode(tag="div", attrib={})
        wrapper.add_child(Text("Important text"))
        wrapper.add_child(DomNode(tag="span", attrib={"id": "child"}))

        result = _collapse_non_semantic_wrappers(wrapper)

        # Wrapper has meaningful text, so it should not be collapsed
        assert result.tag == "div"
        assert len(result.children) == 2

    def test_collapses_with_whitespace_only_text(self):
        """Test collapses wrapper with only whitespace text."""
        wrapper = DomNode(tag="div", attrib={})
        wrapper.add_child(Text("   \n\t   "))
        wrapper.add_child(DomNode(tag="span", attrib={"id": "child"}))

        result = _collapse_non_semantic_wrappers(wrapper)

        # Whitespace-only text doesn't count as meaningful, so collapse
        # Result should be the span
        assert result.tag == "span"
        assert result.attrib == {"id": "child"}

    def test_keeps_element_with_only_text_children(self):
        """Test keeps element with only text children (no element children)."""
        node = DomNode(tag="p", attrib={})
        node.add_child(Text("Hello"))
        node.add_child(Text(" World"))

        result = _collapse_non_semantic_wrappers(node)

        # No element children (len(element_children) != 1), so keep as-is
        assert result.tag == "p"
        assert len(result.children) == 2

    def test_recursively_collapses_nested_wrappers(self):
        """Test recursively collapses nested wrapper elements."""
        # outer > middle > inner
        outer = DomNode(tag="div", attrib={})
        middle = DomNode(tag="section", attrib={})
        inner = DomNode(tag="span", attrib={"id": "inner"})

        middle.add_child(inner)
        outer.add_child(middle)

        result = _collapse_non_semantic_wrappers(outer)

        # Both outer and middle should be collapsed, leaving only inner
        assert result.tag == "span"
        assert result.attrib == {"id": "inner"}

    def test_partially_collapses_mixed_structure(self):
        """Test partially collapses when only some wrappers are collapsible."""
        # root (has semantic attrib) > wrapper1 (no attrib, 1 child) > wrapper2 (no attrib, 1 child) > leaf
        root = DomNode(tag="div", attrib={"role": "main"})
        wrapper1 = DomNode(tag="section", attrib={})
        wrapper2 = DomNode(tag="article", attrib={})
        leaf = DomNode(tag="span", attrib={"role": "button"})

        wrapper2.add_child(leaf)
        wrapper1.add_child(wrapper2)
        root.add_child(wrapper1)

        result = _collapse_non_semantic_wrappers(root)

        # Root has semantic attributes, so it's kept
        # wrapper1 and wrapper2 should be collapsed
        assert result.tag == "div"
        assert result.attrib == {"role": "main"}
        assert len(result.children) == 1
        # Child should be the leaf (wrappers collapsed)
        assert result.children[0].tag == "span"
        assert result.children[0].attrib == {"role": "button"}

    def test_preserves_text_children_in_result(self):
        """Test preserves text children when not collapsing."""
        node = DomNode(tag="div", attrib={"id": "test"})
        node.add_child(Text("Text content"))

        result = _collapse_non_semantic_wrappers(node)

        # Not collapsed because no element children
        assert result.tag == "div"
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)

    def test_empty_wrapper_not_collapsed(self):
        """Test empty wrapper (no children) is not collapsed."""
        wrapper = DomNode(tag="div", attrib={})

        result = _collapse_non_semantic_wrappers(wrapper)

        # No element children (len != 1), so not collapsed
        assert result.tag == "div"
        assert len(result.children) == 0

    def test_wrapper_with_single_text_child_not_collapsed(self):
        """Test wrapper with only a single text child is not collapsed."""
        wrapper = DomNode(tag="p", attrib={})
        wrapper.add_child(Text("Just text"))

        result = _collapse_non_semantic_wrappers(wrapper)

        # No element children (len != 1), so not collapsed
        assert result.tag == "p"
        assert len(result.children) == 1

    def test_creates_new_node(self):
        """Test creates new nodes when not collapsing."""
        original = DomNode(tag="div", attrib={"role": "group"})
        child = DomNode(tag="span")
        original.add_child(child)

        result = _collapse_non_semantic_wrappers(original)

        # Should NOT collapse because div has semantic attributes
        # Creates new node copy instead
        assert result.tag == "div"
        assert result.attrib == {"role": "group"}
        assert len(result.children) == 1
        assert result.children[0].tag == "span"
