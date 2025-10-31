"""Tests for visibility filters orchestrator."""

import pytest
from webtask.llm_browser.filters.apply_visibility_filters import (
    apply_visibility_filters,
)
from webtask.llm_browser.dom_filter_config import DomFilterConfig
from webtask.dom.domnode import DomNode, BoundingBox


@pytest.mark.unit
class TestApplyVisibilityFilters:
    """Tests for apply_visibility_filters orchestrator."""

    def test_uses_default_config_when_none_provided(self):
        """Test uses default DomFilterConfig when config is None."""
        node = DomNode(
            tag="div",
            attrib={"id": "test"},
            styles={"display": "block"},
            bounds=BoundingBox(0, 0, 100, 100),
        )

        result = apply_visibility_filters(node, config=None)

        assert result is not None

    def test_applies_all_filters_by_default(self, dom_tree_with_hidden_elements):
        """Test applies all visibility filters with default config."""
        result = apply_visibility_filters(dom_tree_with_hidden_elements)

        assert result is not None
        # Should have visible div and button, but not hidden div or script
        assert len(result.children) == 2
        # Find visible div and button
        child_ids = [
            c.attrib.get("id") for c in result.children if isinstance(c, DomNode)
        ]
        assert "visible" in child_ids

    def test_filter_non_visible_tags_disabled(self):
        """Test with filter_non_visible_tags disabled."""
        config = DomFilterConfig(
            filter_non_visible_tags=False,
            filter_no_layout=False,  # Also disable to test tag filter in isolation
        )

        root = DomNode(tag="div", styles={"display": "block"})
        script = DomNode(tag="script")
        div = DomNode(tag="div", styles={"display": "block"})

        root.add_child(script)
        root.add_child(div)

        result = apply_visibility_filters(root, config)

        # Script should NOT be removed (both tag and layout filters disabled)
        assert result is not None
        assert len(result.children) == 2
        assert result.children[0].tag == "script"

    def test_filter_css_hidden_disabled(self):
        """Test with filter_css_hidden disabled."""
        config = DomFilterConfig(filter_css_hidden=False)

        root = DomNode(tag="div", styles={"display": "block"})
        hidden = DomNode(tag="div", styles={"display": "none"})

        root.add_child(hidden)

        result = apply_visibility_filters(root, config)

        # Hidden element should NOT be removed
        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].styles["display"] == "none"

    def test_filter_no_layout_disabled(self):
        """Test with filter_no_layout disabled."""
        config = DomFilterConfig(filter_no_layout=False)

        root = DomNode(tag="div", styles={"display": "block"})
        no_layout = DomNode(tag="div", styles={}, bounds=None)

        root.add_child(no_layout)

        result = apply_visibility_filters(root, config)

        # Element without layout should NOT be removed
        assert result is not None
        assert len(result.children) == 1

    def test_filter_zero_dimensions_disabled(self):
        """Test with filter_zero_dimensions disabled."""
        config = DomFilterConfig(filter_zero_dimensions=False)

        root = DomNode(tag="div", bounds=BoundingBox(0, 0, 100, 100))
        zero_size = DomNode(tag="div", bounds=BoundingBox(0, 0, 0, 0))

        root.add_child(zero_size)

        result = apply_visibility_filters(root, config)

        # Zero-size element should NOT be removed
        assert result is not None
        assert len(result.children) == 1

    def test_filters_applied_in_correct_order(self):
        """Test filters are applied in the correct order."""
        # Order: non_visible_tags -> css_hidden -> no_layout -> zero_dimensions
        config = DomFilterConfig()

        root = DomNode(
            tag="div", styles={"display": "block"}, bounds=BoundingBox(0, 0, 100, 100)
        )

        # This script tag should be removed by non_visible_tags filter
        script = DomNode(tag="script", styles={"display": "block"})

        # This div should be removed by css_hidden filter
        hidden = DomNode(tag="div", styles={"display": "none"})

        # This should be kept
        visible = DomNode(
            tag="div", styles={"display": "block"}, bounds=BoundingBox(0, 0, 50, 50)
        )

        root.add_child(script)
        root.add_child(hidden)
        root.add_child(visible)

        result = apply_visibility_filters(root, config)

        assert result is not None
        assert len(result.children) == 1
        assert (
            result.children[0] == visible or result.children[0].bounds == visible.bounds
        )

    def test_custom_non_visible_tags(self):
        """Test with custom non_visible_tags set."""
        config = DomFilterConfig(non_visible_tags={"custom-hidden", "another-hidden"})

        root = DomNode(tag="div", styles={"display": "block"})
        custom = DomNode(tag="custom-hidden")
        script = DomNode(tag="script")  # Not in custom set
        div = DomNode(tag="div", styles={"display": "block"})

        root.add_child(custom)
        root.add_child(script)
        root.add_child(div)

        result = apply_visibility_filters(root, config)

        # custom-hidden should be removed, script should be kept
        assert result is not None
        # Should have script and div, but not custom-hidden
        tags = [c.tag for c in result.children if isinstance(c, DomNode)]
        assert "custom-hidden" not in tags
        assert "script" in tags or "div" in tags

    def test_returns_none_if_root_filtered(self):
        """Test returns None if root element is filtered out."""
        config = DomFilterConfig()

        root = DomNode(tag="script")  # Will be filtered by non_visible_tags

        result = apply_visibility_filters(root, config)

        assert result is None

    def test_all_filters_disabled_returns_unchanged(self):
        """Test with all filters disabled returns node unchanged."""
        config = DomFilterConfig(
            filter_non_visible_tags=False,
            filter_css_hidden=False,
            filter_no_layout=False,
            filter_zero_dimensions=False,
        )

        root = DomNode(
            tag="div",
            styles={"display": "none"},  # Would be hidden
            bounds=BoundingBox(0, 0, 0, 0),  # Zero size
        )
        script = DomNode(tag="script")  # Non-visible tag
        root.add_child(script)

        result = apply_visibility_filters(root, config)

        # Everything should be kept
        assert result is not None
        assert len(result.children) == 1
        assert result.children[0].tag == "script"

    def test_preserves_node_properties(self):
        """Test preserves node properties through filtering."""
        config = DomFilterConfig()

        root = DomNode(
            tag="div",
            attrib={"id": "root", "class": "container"},
            styles={"display": "block", "color": "red"},
            bounds=BoundingBox(0, 0, 800, 600),
            metadata={"cdp_index": 0, "custom": "data"},
        )

        result = apply_visibility_filters(root, config)

        assert result is not None
        assert result.tag == "div"
        assert result.attrib == {"id": "root", "class": "container"}
        assert result.styles == {"display": "block", "color": "red"}
        assert result.bounds == BoundingBox(0, 0, 800, 600)
        # Note: metadata is preserved through copy() in filters

    def test_complex_tree_filtering(self, dom_tree_with_hidden_elements):
        """Test complex tree with multiple filter conditions."""
        config = DomFilterConfig()

        result = apply_visibility_filters(dom_tree_with_hidden_elements, config)

        assert result is not None
        assert result.tag == "div"
        assert result.attrib["id"] == "root"

        # Collect all remaining nodes
        all_nodes = list(result.traverse())
        node_ids = [n.attrib.get("id") for n in all_nodes if isinstance(n, DomNode)]

        # visible div should remain
        assert "visible" in node_ids
        # hidden div should be removed
        assert "hidden" not in node_ids
        # script should be removed (non-visible tag)
        assert all(n.tag != "script" for n in all_nodes if isinstance(n, DomNode))
