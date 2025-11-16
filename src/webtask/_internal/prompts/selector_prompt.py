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
            "Review the page context showing available elements with their interactive_ids"
        )
        .add_numbered(
            "Compare the user's description with each element's attributes and text"
        )
        .add_numbered("Identify the interactive_id that best matches the description")
        .add_numbered("Return the interactive_id or an error if no match found")
    )

    return (
        MarkdownBuilder()
        .add(who_you_are)
        .add()
        .add(how_to_select)
        .build()
    )
