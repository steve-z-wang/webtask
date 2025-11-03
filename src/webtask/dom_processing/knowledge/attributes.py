"""Knowledge: Determine if attributes are semantic.

Pure function that answers: "Is this attribute semantically meaningful?"
Based on web standards - attributes that provide useful information about element behavior.
"""

# Semantic attributes that provide meaningful information for the LLM
SEMANTIC_ATTRIBUTES = {
    # ARIA attributes (accessibility/interactivity)
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-checked",
    "aria-selected",
    "aria-expanded",
    "aria-hidden",
    "aria-disabled",
    "aria-haspopup",  # Indicates interactive popup/menu elements
    # Form/input attributes
    "type",
    "name",
    "placeholder",
    "value",
    "accept",  # File input accepted types (e.g., "image/*")
    "alt",
    "title",
    "disabled",
    "checked",
    "selected",
    # Interaction attributes
    "tabindex",  # Keyboard focusable
    "onclick",  # Click handler
}


def is_semantic_attribute(attr_name: str) -> bool:
    """Check if an attribute is semantically meaningful.

    Semantic attributes provide useful information about element behavior,
    purpose, or state. Non-semantic attributes (like styling or IDs) are noise.

    Args:
        attr_name: Attribute name to check

    Returns:
        True if attribute is semantic and should be kept, False otherwise

    Example:
        >>> is_semantic_attribute("type")
        True
        >>> is_semantic_attribute("role")
        True
        >>> is_semantic_attribute("class")
        False
        >>> is_semantic_attribute("style")
        False
    """
    return attr_name in SEMANTIC_ATTRIBUTES
