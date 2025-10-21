"""Context and Block classes for LLM prompts."""

from typing import List, Union


class Block:
    """
    Building block for LLM context.

    Blocks can contain text and nested blocks, allowing composable context construction.
    """

    def __init__(self, text: str = ""):
        """
        Create a Block with optional text.

        Args:
            text: Text content for this block
        """
        self.text = text
        self.blocks: List['Block'] = []

    def append(self, item: Union['Block', str]) -> 'Block':
        """
        Append a nested block or text.

        Args:
            item: Block or string to append

        Returns:
            Self for chaining
        """
        if isinstance(item, str):
            item = Block(item)
        self.blocks.append(item)
        return self

    def __str__(self) -> str:
        """
        Render block and all nested blocks to text.

        Returns:
            Formatted text with nested blocks separated by double newlines
        """
        parts = []
        if self.text:
            parts.append(self.text)
        for block in self.blocks:
            parts.append(str(block))
        return "\n\n".join(parts)


class Context:
    """
    LLM context with system and user prompts.

    User prompt is built from composable Blocks.
    """

    def __init__(self, system: str = ""):
        """
        Create a Context with system prompt.

        Args:
            system: System prompt text
        """
        self.system = system
        self.blocks: List[Block] = []

    def append(self, item: Union[Block, str]) -> 'Context':
        """
        Append a block or string to user prompt.

        Args:
            item: Block or string to append

        Returns:
            Self for chaining
        """
        if isinstance(item, str):
            item = Block(item)
        self.blocks.append(item)
        return self

    @property
    def user(self) -> str:
        """
        Get user prompt as string.

        Returns:
            Rendered user prompt from all blocks
        """
        if not self.blocks:
            return ""
        parts = [str(block) for block in self.blocks]
        return "\n\n".join(parts)

    def __str__(self) -> str:
        """
        Get full context (system + user) as string.

        Returns:
            Formatted context with system and user prompts
        """
        parts = []
        if self.system:
            parts.append(f"System:\n{self.system}")
        if self.user:
            parts.append(f"User:\n{self.user}")
        return "\n\n".join(parts)
