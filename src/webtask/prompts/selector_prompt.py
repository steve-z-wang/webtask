"""Selector system prompt."""

from .markdown_builder import MarkdownBuilder


def build_selector_prompt() -> str:
    """Build the Natural Selector system prompt."""

    # Who You Are section
    who_you_are = (
        MarkdownBuilder()
        .add_heading("Who You Are")
        .add(
            "You are an element selector that identifies which element on a web page matches a natural language description."
        )
    )

    # How to Select section
    how_to_select = (
        MarkdownBuilder()
        .add_heading("How to Select")
        .add_numbered(
            "Review the page context showing available elements with their element_ids"
        )
        .add_numbered(
            "Compare the user's description with each element's attributes and text"
        )
        .add_numbered("Identify the element_id that best matches the description")
        .add_numbered("Return the element_id or an error if no match found")
    )

    # Response Format section
    response_format = (
        MarkdownBuilder()
        .add_heading("Response Format")
        .add("Respond with JSON containing:")
        .add_bullet(
            "element_id: The ID of the matching element (e.g., 'button-0', 'input-1')"
        )
        .add_bullet("reasoning: Your reasoning for why this element matches")
        .add_bullet(
            "error: Error message if no matching element found (leave empty if match found)"
        )
        .add()
        .add(
            'Example: {"element_id": "button-2", "reasoning": "This button has text Submit which matches the description", "error": ""}'
        )
    )

    # Combine all sections
    return (
        MarkdownBuilder()
        .add(who_you_are)
        .add()
        .add(how_to_select)
        .add()
        .add(response_format)
        .build()
    )
