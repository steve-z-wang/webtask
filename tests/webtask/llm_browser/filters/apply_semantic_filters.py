"""Tests for semantic filters orchestrator."""

import pytest
from webtask.llm_browser.filters.apply_semantic_filters import apply_semantic_filters
from webtask.llm_browser.dom_filter_config import DomFilterConfig
from webtask.dom.domnode import DomNode, Text


@pytest.mark.unit
class TestApplySemanticFilters:
    """Tests for apply_semantic_filters orchestrator."""

    def test_uses_default_config_when_none_provided(self):
        """Test uses default DomFilterConfig when config is None."""
        node = DomNode(
            tag="div",
            attrib={"role": "banner", "class": "foo"},
        )

        result = apply_semantic_filters(node, config=None)

        assert result is not None
        # With default config, non-kept attributes should be removed
        # Default kept_attributes includes 'role' but not 'class'
        assert "role" in result.attrib
        assert "class" not in result.attrib

    def test_applies_all_filters_by_default(self):
        """Test applies all semantic filters with default config."""
        # Create a node that will be affected by multiple filters
        root = DomNode(
            tag="div",
            attrib={
                "role": "banner",  # Will be kept (semantic)
                "class": "container",  # Will be removed (not in kept_attributes)
            },
        )

        # Empty wrapper
        wrapper = DomNode(tag="section", attrib={})
        # Actual content (interactive element kept even without attributes)
        content = DomNode(tag="button", attrib={})

        wrapper.add_child(content)
        root.add_child(wrapper)

        result = apply_semantic_filters(root)

        assert result is not None
        # class removed by filter_attributes
        assert "class" not in result.attrib
        # role kept (semantic)
        assert result.attrib["role"] == "banner"
        # wrapper collapsed by collapse_wrappers
        assert len(result.children) == 1
        assert result.children[0].tag == "button"

    def test_filter_attributes_disabled(self):
        """Test with filter_attributes disabled."""
        config = DomFilterConfig(filter_attributes=False)

        node = DomNode(
            tag="div",
            attrib={"id": "test", "class": "foo", "data-x": "y"},
        )

        result = apply_semantic_filters(node, config)

        # All attributes should be kept
        assert result.attrib == {"id": "test", "class": "foo", "data-x": "y"}

    def test_filter_presentational_roles_disabled(self):
        """Test with filter_presentational_roles disabled."""
        config = DomFilterConfig(filter_presentational_roles=False)

        node = DomNode(
            tag="div",
            attrib={"role": "none"},
        )

        result = apply_semantic_filters(node, config)

        # role='none' should be kept
        assert "role" in result.attrib
        assert result.attrib["role"] == "none"

    def test_filter_empty_disabled(self):
        """Test with filter_empty disabled."""
        config = DomFilterConfig(filter_empty=False)

        empty_div = DomNode(tag="div", attrib={})

        result = apply_semantic_filters(empty_div, config)

        # Empty div should be kept
        assert result is not None
        assert result.tag == "div"

    def test_collapse_wrappers_disabled(self):
        """Test with collapse_wrappers disabled."""
        config = DomFilterConfig(collapse_wrappers=False)

        wrapper = DomNode(tag="div", attrib={})
        child = DomNode(tag="button", attrib={})  # Interactive element
        wrapper.add_child(child)

        result = apply_semantic_filters(wrapper, config)

        # Wrapper should not be collapsed
        assert result.tag == "div"
        assert len(result.children) == 1
        assert result.children[0].tag == "button"

    def test_filters_applied_in_correct_order(self):
        """Test filters are applied in the correct order."""
        # Order: attributes -> presentational_roles -> empty -> wrappers
        config = DomFilterConfig()

        # This will test the order:
        # 1. filter_attributes removes non-kept attributes
        # 2. filter_presentational_roles removes role='none'
        # 3. filter_empty could remove empty elements
        # 4. collapse_wrappers collapses single-child wrappers

        root = DomNode(
            tag="div",
            attrib={
                "role": "main",  # Will be kept
                "class": "test",  # Will be removed
                "data-foo": "bar",  # Will be removed
            },
        )

        wrapper = DomNode(
            tag="section",
            attrib={"role": "presentation"},  # Will be removed (presentational)
        )

        content = DomNode(
            tag="button",  # Interactive element
            attrib={"type": "submit", "style": "color: red"},  # style will be removed
        )

        wrapper.add_child(content)
        root.add_child(wrapper)

        result = apply_semantic_filters(root, config)

        assert result is not None
        # root keeps only 'role' (kept attribute)
        assert result.attrib == {"role": "main"}
        # wrapper should be collapsed (no attributes after filtering)
        assert len(result.children) == 1
        assert result.children[0].attrib == {"type": "submit"}

    def test_custom_kept_attributes(self):
        """Test with custom kept_attributes set."""
        config = DomFilterConfig(kept_attributes={"class", "data-test"})  # Custom set

        node = DomNode(
            tag="div",
            attrib={
                "id": "test",  # Not in custom set
                "class": "foo",  # In custom set
                "data-test": "value",  # In custom set
            },
        )

        result = apply_semantic_filters(node, config)

        # Only class and data-test should be kept
        assert result.attrib == {"class": "foo", "data-test": "value"}
        assert "id" not in result.attrib

    def test_custom_interactive_tags(self):
        """Test with custom interactive_tags set."""
        config = DomFilterConfig(interactive_tags={"custom-button"})  # Custom set

        # Empty custom-button should be kept (interactive)
        custom = DomNode(tag="custom-button", attrib={})
        # Empty button should be removed (not in custom set)
        button = DomNode(tag="button", attrib={})

        result_custom = apply_semantic_filters(custom, config)
        result_button = apply_semantic_filters(button, config)

        assert result_custom is not None  # Kept
        assert result_button is None  # Removed (empty and not interactive)

    def test_returns_none_if_root_filtered(self):
        """Test returns None if root element is filtered out."""
        config = DomFilterConfig()

        # Empty div with no attributes or interactive tag
        empty_root = DomNode(tag="div", attrib={})

        result = apply_semantic_filters(empty_root, config)

        # Should be removed by filter_empty
        assert result is None

    def test_all_filters_disabled_returns_unchanged(self):
        """Test with all filters disabled returns node mostly unchanged."""
        config = DomFilterConfig(
            filter_attributes=False,
            filter_presentational_roles=False,
            filter_empty=False,
            collapse_wrappers=False,
        )

        root = DomNode(
            tag="div",
            attrib={"class": "test", "role": "none"},
        )
        empty_child = DomNode(tag="section", attrib={})
        root.add_child(empty_child)

        result = apply_semantic_filters(root, config)

        # Everything should be kept
        assert result is not None
        assert result.attrib == {"class": "test", "role": "none"}
        assert len(result.children) == 1

    def test_complex_nested_structure(self):
        """Test with complex nested structure."""
        config = DomFilterConfig()

        root = DomNode(tag="div", attrib={"role": "main", "class": "container"})

        # Level 1: wrapper (should collapse)
        wrapper1 = DomNode(tag="section", attrib={})

        # Level 2: wrapper with role='presentation' (should collapse and role removed)
        wrapper2 = DomNode(tag="article", attrib={"role": "presentation"})

        # Level 3: actual content with text
        content = DomNode(tag="p", attrib={})
        content.add_child(Text("Content"))

        # Level 3: empty div (should be removed)
        empty = DomNode(tag="div", attrib={})

        wrapper2.add_child(content)
        wrapper2.add_child(empty)
        wrapper1.add_child(wrapper2)
        root.add_child(wrapper1)

        result = apply_semantic_filters(root, config)

        assert result is not None
        assert result.attrib == {"role": "main"}  # class removed
        # Wrappers should be collapsed, empty removed
        # Let's verify content is present
        all_nodes = list(result.traverse())
        # Find the p tag with text
        p_nodes = [n for n in all_nodes if isinstance(n, DomNode) and n.tag == "p"]
        assert len(p_nodes) >= 1

    def test_preserves_node_properties(self):
        """Test preserves node properties through filtering."""
        from webtask.dom.domnode import BoundingBox

        config = DomFilterConfig()

        node = DomNode(
            tag="div",
            attrib={"role": "region", "class": "foo"},
            styles={"display": "block", "color": "red"},
            bounds=BoundingBox(0, 0, 800, 600),
            metadata={"cdp_index": 42},
        )

        result = apply_semantic_filters(node, config)

        assert result is not None
        # Attributes filtered
        assert "role" in result.attrib
        assert "class" not in result.attrib
        # Other properties preserved
        assert result.tag == "div"
        assert result.styles == {"display": "block", "color": "red"}
        assert result.bounds == BoundingBox(0, 0, 800, 600)
