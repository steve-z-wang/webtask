"""Tests for presentational roles filter."""

import pytest
from webtask.llm_browser.filters.semantic.presentational import (
    filter_presentational_roles,
)
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestFilterPresentationalRoles:
    """Tests for filter_presentational_roles function."""

    def test_removes_role_none(self):
        """Test removes role='none' attribute."""
        node = DomNode(
            tag="div",
            attrib={"id": "test", "role": "none"},
        )

        result = filter_presentational_roles(node)

        assert "role" not in result.attrib
        assert result.attrib == {"id": "test"}

    def test_removes_role_presentation(self):
        """Test removes role='presentation' attribute."""
        node = DomNode(
            tag="div",
            attrib={"id": "test", "role": "presentation"},
        )

        result = filter_presentational_roles(node)

        assert "role" not in result.attrib
        assert result.attrib == {"id": "test"}

    def test_keeps_semantic_roles(self):
        """Test keeps semantic role attributes."""
        node = DomNode(
            tag="div",
            attrib={"id": "test", "role": "button"},
        )

        result = filter_presentational_roles(node)

        assert result.attrib == {"id": "test", "role": "button"}

    def test_case_insensitive_matching(self):
        """Test role matching is case-insensitive."""
        node1 = DomNode(tag="div", attrib={"role": "NONE"})
        node2 = DomNode(tag="div", attrib={"role": "Presentation"})
        node3 = DomNode(tag="div", attrib={"role": "None"})

        result1 = filter_presentational_roles(node1)
        result2 = filter_presentational_roles(node2)
        result3 = filter_presentational_roles(node3)

        assert "role" not in result1.attrib
        assert "role" not in result2.attrib
        assert "role" not in result3.attrib

    def test_keeps_non_presentational_roles_case_insensitive(self):
        """Test keeps non-presentational roles regardless of case."""
        node = DomNode(tag="div", attrib={"role": "BUTTON"})

        result = filter_presentational_roles(node)

        # Role should be kept but original case preserved
        assert "role" in result.attrib
        assert result.attrib["role"] == "BUTTON"

    def test_filters_children_recursively(self):
        """Test filters children recursively."""
        root = DomNode(
            tag="div",
            attrib={"role": "none"},
        )

        child1 = DomNode(
            tag="span",
            attrib={"role": "presentation", "id": "c1"},
        )

        child2 = DomNode(
            tag="button",
            attrib={"role": "button", "id": "c2"},
        )

        root.add_child(child1)
        root.add_child(child2)

        result = filter_presentational_roles(root)

        # Root role removed
        assert "role" not in result.attrib
        # Child1 role removed
        assert "role" not in result.children[0].attrib
        assert result.children[0].attrib == {"id": "c1"}
        # Child2 role kept
        assert result.children[1].attrib == {"role": "button", "id": "c2"}

    def test_preserves_text_children(self):
        """Test preserves text children."""
        node = DomNode(
            tag="div",
            attrib={"role": "none"},
        )
        node.add_child(Text("Hello"))

        result = filter_presentational_roles(node)

        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)
        assert result.children[0].content == "Hello"

    def test_node_without_role_unchanged(self):
        """Test nodes without role attribute are unchanged."""
        node = DomNode(
            tag="div",
            attrib={"id": "test", "class": "foo"},
        )

        result = filter_presentational_roles(node)

        assert result.attrib == {"id": "test", "class": "foo"}

    def test_preserves_other_node_properties(self):
        """Test preserves all node properties."""
        from webtask.dom.domnode import BoundingBox

        node = DomNode(
            tag="div",
            attrib={"role": "none", "id": "test"},
            styles={"display": "block"},
            bounds=BoundingBox(10, 10, 100, 50),
            metadata={"cdp_index": 42},
        )

        result = filter_presentational_roles(node)

        assert result.attrib == {"id": "test"}
        assert result.tag == "div"
        assert result.styles == {"display": "block"}
        assert result.bounds == BoundingBox(10, 10, 100, 50)
        assert result.metadata == {"cdp_index": 42}

    def test_creates_new_node(self):
        """Test creates a new node without modifying original."""
        original = DomNode(
            tag="div",
            attrib={"role": "none", "id": "test"},
        )

        result = filter_presentational_roles(original)

        # Result has role removed
        assert "role" not in result.attrib
        # Original unchanged
        assert original.attrib == {"role": "none", "id": "test"}
        # Different objects
        assert result is not original

    def test_empty_role_value(self):
        """Test handles empty role value."""
        node = DomNode(
            tag="div",
            attrib={"role": "", "id": "test"},
        )

        result = filter_presentational_roles(node)

        # Empty string is not 'none' or 'presentation', so it's kept
        assert result.attrib == {"role": "", "id": "test"}

    def test_whitespace_in_role_value(self):
        """Test handles whitespace in role value."""
        node1 = DomNode(tag="div", attrib={"role": " none "})
        node2 = DomNode(tag="div", attrib={"role": " presentation "})

        result1 = filter_presentational_roles(node1)
        result2 = filter_presentational_roles(node2)

        # Whitespace is not trimmed, so these won't match 'none'/'presentation'
        # Actually, wait - let me check the code again
        # The code does .lower() but doesn't strip(), so these should NOT match
        assert "role" in result1.attrib  # ' none ' != 'none'
        assert "role" in result2.attrib  # ' presentation ' != 'presentation'
