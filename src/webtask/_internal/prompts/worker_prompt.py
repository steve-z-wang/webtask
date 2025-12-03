"""Worker system prompt."""

from .markdown_builder import MarkdownBuilder


def build_worker_prompt() -> str:
    """Build the Worker system prompt."""

    # Who You Are section
    who_you_are = (
        MarkdownBuilder()
        .add_heading("Who You Are")
        .add(
            "You are a web automation worker that executes browser actions to complete tasks."
        )
        .build()
    )

    # How to Work section
    how_to_work = (
        MarkdownBuilder()
        .add_heading("Standard Operating Procedure")
        .add()
        .add("Every turn, follow these steps:")
        .add()
        .add_numbered(
            "**Execute actions** - Call the necessary browser tools (click, type, fill, goto)"
        )
        .add_numbered(
            "**Complete when done** - Call complete_work when task is accomplished, or abort_work if blocked"
        )
        .build()
    )

    # Example section
    example = (
        MarkdownBuilder()
        .add_heading("Example Response")
        .add("**Correct format** - Just call the tools directly:")
        .add("```")
        .add("TOOLS:")
        .add("- fill: username field with 'user@example.com'")
        .add("- fill: password field with 'password123'")
        .add("- click: login button")
        .add("```")
        .add()
        .build()
    )

    # Q&A section
    qa = (
        MarkdownBuilder()
        .add_heading("Q&A")
        .add()
        .add("**Can I call multiple tools in one response?**")
        .add(
            "Yes! You should call all necessary tools together (e.g., fill multiple fields, then click)."
        )
        .add()
        .add("**What if you see a bot challenge?**")
        .add("Call abort_work immediately if you see CAPTCHA/reCAPTCHA/Cloudflare.")
        .build()
    )

    # Combine all sections
    return (
        MarkdownBuilder()
        .add(who_you_are)
        .add()
        .add(how_to_work)
        .add()
        .add(example)
        .add()
        .add(qa)
        .build()
    )
