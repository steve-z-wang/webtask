"""MarkdownBuilder - simple markdown text composition."""


class MarkdownBuilder:
    """Builder for composing markdown text.

    Example:
        prompt = (
            MarkdownBuilder()
            .add_heading("How to Work")
            .add_numbered("Check history")
            .add_numbered("Observe page")
            .add_blank()
            .add_heading("Important")
            .add_bullet("Point 1")
            .add_bullet("Point 2")
            .build()
        )
    """

    def __init__(self):
        self.lines = []
        self._number = 1
        self._last_was_numbered = False

    def add_heading(self, text: str, level: int = 2) -> "MarkdownBuilder":
        """Add a markdown heading."""
        self.lines.append(f"{'#' * level} {text}")
        self._number = 1  # Reset numbering after heading
        self._last_was_numbered = False
        return self

    def add(self, content="") -> "MarkdownBuilder":
        """Add a line or another MarkdownBuilder's content."""
        if isinstance(content, MarkdownBuilder):
            # Add the other builder's content
            self.lines.append(content.build())
        else:
            self.lines.append(str(content))

        # Reset numbering since this wasn't a numbered line
        self._number = 1
        self._last_was_numbered = False
        return self

    def add_bullet(self, text: str) -> "MarkdownBuilder":
        """Add a bullet point."""
        self.lines.append(f"- {text}")
        self._number = 1  # Reset numbering
        self._last_was_numbered = False
        return self

    def add_numbered(self, text: str) -> "MarkdownBuilder":
        """Add a numbered item. Auto-increments.

        Auto-resets to 1 if previous line wasn't numbered.
        """
        # Reset numbering if previous line wasn't numbered
        if not self._last_was_numbered:
            self._number = 1

        self.lines.append(f"{self._number}. {text}")
        self._number += 1
        self._last_was_numbered = True
        return self

    def build(self) -> str:
        """Build the final markdown string."""
        return "\n".join(self.lines)
