"""Knowledge: Determine if elements/roles are presentational.

Pure function that answers: "Is this element/role purely presentational (no semantic meaning)?"
Based on ARIA specification.
"""

from ...dom.domnode import DomNode


def is_presentational_role(node: DomNode) -> bool:
    """Check if element has a presentational ARIA role.

    ARIA roles "none" and "presentation" indicate that an element is purely decorative
    and should be ignored by assistive technologies (screen readers).

    Args:
        node: DOM node to check

    Returns:
        True if element has role="none" or role="presentation", False otherwise

    Example:
        >>> node = DomNode(tag="div", attrib={"role": "presentation"})
        >>> is_presentational_role(node)
        True

        >>> node = DomNode(tag="div", attrib={"role": "button"})
        >>> is_presentational_role(node)
        False
    """
    role = node.attrib.get("role", "").lower()
    return role in ("none", "presentation")
