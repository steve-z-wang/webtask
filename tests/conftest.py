"""Pytest configuration and shared fixtures."""

import pytest
from typing import Dict, Any
from webtask._internal.dom.domnode import DomNode, Text, BoundingBox


@pytest.fixture
def sample_cdp_snapshot() -> Dict[str, Any]:
    """
    Sample CDP snapshot data for testing.

    Represents a simple DOM:
    <html>
      <div id="container">Hello</div>
      <button>Click</button>
    </html>
    """
    return {
        "documents": [
            {
                "nodes": {
                    "nodeType": [
                        9,
                        1,
                        1,
                        3,
                        1,
                        3,
                    ],  # Document, html, div, text, button, text
                    "nodeName": [-1, 0, 1, -1, 2, -1],  # Indices into strings
                    "nodeValue": [-1, -1, -1, 3, -1, 4],
                    "parentIndex": [-1, 0, 1, 2, 1, 4],
                    "attributes": [
                        [],  # document
                        [],  # html
                        [5, 6],  # div: id="container"
                        [],  # text
                        [],  # button
                        [],  # text
                    ],
                },
                "layout": {
                    "nodeIndex": [1, 2, 4],  # html, div, button have layout
                    "bounds": [
                        [0, 0, 1024, 768],  # html
                        [10, 10, 200, 50],  # div
                        [10, 70, 100, 30],  # button
                    ],
                    "styles": [
                        [7, 8, 9],  # html: display=block, visibility=visible, opacity=1
                        [7, 8, 9],  # div: display=block, visibility=visible, opacity=1
                        [
                            7,
                            8,
                            9,
                        ],  # button: display=block, visibility=visible, opacity=1
                    ],
                },
            }
        ],
        "strings": [
            "html",  # 0
            "div",  # 1
            "button",  # 2
            "Hello",  # 3
            "Click",  # 4
            "id",  # 5
            "container",  # 6
            "block",  # 7
            "visible",  # 8
            "1",  # 9
        ],
    }


@pytest.fixture
def simple_dom_tree():
    """
    Create a simple DomNode tree for testing.

    Structure:
    <div id="root">
      <h1>Title</h1>
      <button id="submit">Click me</button>
    </div>
    """
    root = DomNode(
        tag="div",
        attrib={"id": "root"},
        bounds=BoundingBox(0, 0, 800, 600),
        metadata={"cdp_index": 0},
    )

    heading = DomNode(
        tag="h1",
        attrib={},
        bounds=BoundingBox(10, 10, 200, 30),
        metadata={"cdp_index": 1},
    )
    heading.add_child(Text("Title"))

    button = DomNode(
        tag="button",
        attrib={"id": "submit"},
        bounds=BoundingBox(10, 50, 100, 30),
        metadata={"cdp_index": 2},
    )
    button.add_child(Text("Click me"))

    root.add_child(heading)
    root.add_child(button)

    return root


@pytest.fixture
def visible_element():
    """Element that is visible (no hiding styles)."""
    return DomNode(
        tag="div",
        attrib={"id": "visible"},
        styles={"display": "block", "visibility": "visible", "opacity": "1"},
        bounds=BoundingBox(10, 10, 100, 50),
        metadata={"cdp_index": 0},
    )


@pytest.fixture
def hidden_display_none():
    """Element hidden with display: none."""
    return DomNode(
        tag="div",
        attrib={"id": "hidden-display"},
        styles={"display": "none"},
        bounds=BoundingBox(0, 0, 0, 0),
        metadata={"cdp_index": 1},
    )


@pytest.fixture
def hidden_visibility_hidden():
    """Element hidden with visibility: hidden."""
    return DomNode(
        tag="div",
        attrib={"id": "hidden-visibility"},
        styles={"visibility": "hidden"},
        bounds=BoundingBox(10, 10, 100, 50),
        metadata={"cdp_index": 2},
    )


@pytest.fixture
def hidden_opacity_zero():
    """Element hidden with opacity: 0."""
    return DomNode(
        tag="div",
        attrib={"id": "hidden-opacity"},
        styles={"opacity": "0"},
        bounds=BoundingBox(10, 10, 100, 50),
        metadata={"cdp_index": 3},
    )


@pytest.fixture
def zero_size_element():
    """Element with zero width/height."""
    return DomNode(
        tag="div",
        attrib={"id": "zero-size"},
        styles={"display": "block"},
        bounds=BoundingBox(10, 10, 0, 0),
        metadata={"cdp_index": 4},
    )


@pytest.fixture
def interactive_elements():
    """List of interactive elements that should be kept."""
    return [
        DomNode(tag="button", attrib={"id": "btn1"}),
        DomNode(tag="input", attrib={"type": "text"}),
        DomNode(tag="a", attrib={"href": "#"}),
        DomNode(tag="select", attrib={"id": "dropdown"}),
        DomNode(tag="textarea", attrib={"id": "comment"}),
    ]


@pytest.fixture
def non_interactive_elements():
    """List of non-interactive elements that should be filtered."""
    return [
        DomNode(tag="script", attrib={"src": "app.js"}),
        DomNode(tag="style", attrib={}),
        DomNode(tag="meta", attrib={"charset": "utf-8"}),
        DomNode(tag="noscript", attrib={}),
        DomNode(tag="link", attrib={"rel": "stylesheet"}),
    ]


@pytest.fixture
def dom_tree_with_hidden_elements():
    """
    DOM tree with mixed visible and hidden elements.

    Structure:
    <div id="root">
      <div id="visible">Visible content</div>
      <div style="display:none">Hidden</div>
      <button>Click</button>
      <script>console.log('test')</script>
    </div>
    """
    root = DomNode(
        tag="div",
        attrib={"id": "root"},
        styles={"display": "block"},
        bounds=BoundingBox(0, 0, 800, 600),
        metadata={"cdp_index": 0},
    )

    visible_div = DomNode(
        tag="div",
        attrib={"id": "visible"},
        styles={"display": "block"},
        bounds=BoundingBox(10, 10, 200, 50),
        metadata={"cdp_index": 1},
    )
    visible_div.add_child(Text("Visible content"))

    hidden_div = DomNode(
        tag="div",
        attrib={"id": "hidden"},
        styles={"display": "none"},
        bounds=BoundingBox(0, 0, 0, 0),
        metadata={"cdp_index": 2},
    )
    hidden_div.add_child(Text("Hidden"))

    button = DomNode(
        tag="button",
        attrib={},
        styles={"display": "block"},
        bounds=BoundingBox(10, 70, 100, 30),
        metadata={"cdp_index": 3},
    )
    button.add_child(Text("Click"))

    script = DomNode(
        tag="script", attrib={}, styles={}, bounds=None, metadata={"cdp_index": 4}
    )
    script.add_child(Text("console.log('test')"))

    root.add_child(visible_div)
    root.add_child(hidden_div)
    root.add_child(button)
    root.add_child(script)

    return root
