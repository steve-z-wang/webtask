"""Knowledge: Determine if a DOM element is interactive.

Pure function that answers: "Is this element interactive?"
Based on HTML and ARIA web standards.
"""

from ..domnode import DomNode

# Standard interactive HTML tags (from HTML spec)
INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "label"}

# Standard interactive ARIA roles (from ARIA 1.2 spec)
INTERACTIVE_ROLES = {
    "button",
    "link",
    "checkbox",
    "radio",
    "switch",
    "tab",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "option",
    "textbox",
    "searchbox",
    "combobox",
    "slider",
    "spinbutton",
}


def is_interactive(node: DomNode) -> bool:
    """Check if a DOM element is interactive based on web standards.

    An element is considered interactive if it matches any of these criteria:
    1. Tag is a standard interactive HTML element (button, input, a, label, etc.)
    2. Has an interactive ARIA role (role="button", role="link", etc.)
    3. Has tabindex attribute (keyboard focusable - strong signal of interactivity)
    4. Has aria-haspopup attribute (indicates it opens a popup/menu)
    5. Has onclick attribute (has click handler)

    These criteria are based on HTML and ARIA web standards.

    Args:
        node: DOM node to check

    Returns:
        True if element is interactive, False otherwise

    Example:
        >>> node = DomNode(tag="button")
        >>> is_interactive(node)
        True
        >>> node = DomNode(tag="div", attrib={"onclick": "handleClick()"})
        >>> is_interactive(node)
        True
    """
    # Check if tag is interactive (HTML standard)
    if node.tag in INTERACTIVE_TAGS:
        return True

    # Check if role attribute indicates interactivity (ARIA standard)
    element_role = node.attrib.get("role")
    if element_role and element_role in INTERACTIVE_ROLES:
        return True

    # Check for ARIA/HTML attributes that indicate interactivity
    if "tabindex" in node.attrib:  # Keyboard focusable
        return True

    if "aria-haspopup" in node.attrib:  # Opens popup/menu
        return True

    if "onclick" in node.attrib:  # Has click handler
        return True

    return False
