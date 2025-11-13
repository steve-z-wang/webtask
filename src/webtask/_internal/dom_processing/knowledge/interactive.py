
from webtask._internal.dom.domnode import DomNode

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
