"""Context and Block classes for LLM prompts."""

from typing import List, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..media import Image


class Block:
    """
    Building block for LLM context.

    Blocks can contain title, text, images, and nested blocks.
    """

    def __init__(
        self, heading: str = "", content: str = "", image: Optional["Image"] = None
    ):
        """
        Create a Block with optional heading, content and image.

        Args:
            heading: Section heading (rendered as markdown h2)
            content: Content for this block
            image: Optional image (e.g., screenshot with bounding boxes)
        """
        self.heading = heading
        self.content = content
        self.image = image
        self.blocks: List["Block"] = []

    def with_block(self, item: Union["Block", str]) -> "Block":
        """Add a nested block or text.

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
            Formatted text with heading as markdown h2 header
        """
        parts = []
        if self.heading:
            parts.append(f"## {self.heading}")
        if self.content:
            parts.append(self.content)
        for block in self.blocks:
            parts.append(str(block))
        return "\n\n".join(parts)


class Context:
    """
    LLM context with system and user prompts.

    User prompt is built from composable Blocks.
    """

    def __init__(self, system: str = "", user: Optional[List[Block]] = None):
        """
        Create a Context with system prompt and user blocks.

        Args:
            system: System prompt text
            user: Optional list of user blocks
        """
        self.system = system
        self.blocks: List[Block] = user if user is not None else []

    def with_system(self, system: str) -> "Context":
        """Set system prompt for this context.

        Args:
            system: System prompt text

        Returns:
            Self for chaining
        """
        self.system = system
        return self

    def with_block(self, item: Union[Block, str]) -> "Context":
        """Add a block or string to user prompt.

        Args:
            item: Block or string to add

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

    def to_text(self) -> str:
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

    def get_images(self) -> List["Image"]:
        """
        Extract all images from context blocks.

        Returns:
            List of Image objects found in all blocks
        """
        images = []

        def extract_images_from_block(block: Block):
            if block.image:
                images.append(block.image)
            for nested_block in block.blocks:
                extract_images_from_block(nested_block)

        for block in self.blocks:
            extract_images_from_block(block)

        return images

    def __str__(self) -> str:
        """
        Get full context (system + user) as string.

        Returns:
            Formatted context with system and user prompts
        """
        return self.to_text()
