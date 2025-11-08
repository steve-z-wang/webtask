"""SystemPromptBuilder - composable system prompt construction."""

from typing import List, Tuple, Optional


class Section:
    """Builder for creating a section with heading and content parts.

    Example:
        section = (
            Section()
            .with_heading("How It Works")
            .add_bullet("Point 1")
            .add_bullet("Point 2")
        )
    """

    def __init__(self):
        self.heading: Optional[str] = None
        self.parts: List[Tuple[str, str]] = []  # (type, content)

    def with_heading(self, heading: str) -> "Section":
        """Set the section heading.

        Args:
            heading: Section heading text

        Returns:
            Self for chaining
        """
        self.heading = heading
        return self

    def add_paragraph(self, text: str) -> "Section":
        """Add a paragraph of text.

        Args:
            text: Paragraph content

        Returns:
            Self for chaining
        """
        self.parts.append(("paragraph", text))
        return self

    def add_bullet(self, text: str) -> "Section":
        """Add a bullet point.

        Args:
            text: Bullet point text

        Returns:
            Self for chaining
        """
        self.parts.append(("bullet", text))
        return self

    def add_qa(self, question: str, answer: str) -> "Section":
        """Add a Q&A pair.

        Args:
            question: Question text
            answer: Answer text

        Returns:
            Self for chaining
        """
        self.parts.append(("qa", question, answer))
        return self

    def build(self) -> str:
        """Build the section content string."""
        content_parts = []
        current_bullets = []

        for part in self.parts:
            part_type = part[0]

            if part_type == "paragraph":
                # Flush pending bullets first
                if current_bullets:
                    content_parts.append("\n".join(f"- {b}" for b in current_bullets))
                    current_bullets = []
                content_parts.append(part[1])
            elif part_type == "bullet":
                current_bullets.append(part[1])
            elif part_type == "qa":
                # Flush pending bullets first
                if current_bullets:
                    content_parts.append("\n".join(f"- {b}" for b in current_bullets))
                    current_bullets = []
                question, answer = part[1], part[2]
                content_parts.append(f"**{question}**\n{answer}")

        # Flush remaining bullets
        if current_bullets:
            content_parts.append("\n".join(f"- {b}" for b in current_bullets))

        content = "\n\n".join(content_parts)

        if self.heading:
            return f"## {self.heading}\n\n{content}"
        return content


class SystemPromptBuilder:
    """Builder for constructing structured system prompts.

    Example:
        prompt = (
            SystemPromptBuilder()
            .add_section(
                Section()
                .with_heading("Identity")
                .add_paragraph("You are a web automation worker.")
            )
            .build()
        )
    """

    def __init__(self):
        self.sections: List[Section] = []

    def add_section(self, section: Section) -> "SystemPromptBuilder":
        """Add a section.

        Args:
            section: Section object to add

        Returns:
            Self for chaining
        """
        self.sections.append(section)
        return self

    def build(self) -> str:
        """Build the final system prompt string."""
        return "\n\n".join(section.build() for section in self.sections)
