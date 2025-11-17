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
        .build()
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
        .build()
    )

    # Response Format section
    response_format = (
        MarkdownBuilder()
        .add_heading("Response Format")
        .add("Return a JSON object with one of these formats:")
        .add()
        .add("**Success (element found):**")
        .add("```json")
        .add("{")
        .add('  "element_id": "textbox-2",')
        .add(
            '  "reasoning": "This is the description input field based on its role and context"'
        )
        .add("}")
        .add("```")
        .add()
        .add("**Failure (no match):**")
        .add("```json")
        .add("{")
        .add('  "element_id": null,')
        .add('  "error": "No element matches the description \'submit button\'"')
        .add("}")
        .add("```")
        .add()
        .add(
            "**IMPORTANT**: You MUST use the exact element_id from the page context (like `button-0`, `textbox-1`, `input-5`). Do NOT create or modify element IDs."
        )
        .build()
    )

    return (
        MarkdownBuilder()
        .add(who_you_are)
        .add()
        .add(how_to_select)
        .add()
        .add(response_format)
        .build()
    )
