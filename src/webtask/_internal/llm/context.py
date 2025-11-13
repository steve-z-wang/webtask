
from typing import List, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..media import Image


class Block:

    def __init__(
        self, heading: str = "", content: str = "", image: Optional["Image"] = None
    ):
        self.heading = heading
        self.content = content
        self.image = image
        self.blocks: List["Block"] = []

    def with_block(self, item: Union["Block", str]) -> "Block":
        if isinstance(item, str):
            item = Block(item)
        self.blocks.append(item)
        return self

    def __str__(self) -> str:
        parts = []
        if self.heading:
            parts.append(f"## {self.heading}")
        if self.content:
            parts.append(self.content)
        for block in self.blocks:
            parts.append(str(block))
        return "\n\n".join(parts)


class Context:

    def __init__(self, system: str = "", user: Optional[List[Block]] = None):
        self.system = system
        self.blocks: List[Block] = user if user is not None else []

    def with_system(self, system: str) -> "Context":
        self.system = system
        return self

    def with_block(self, item: Union[Block, str]) -> "Context":
        if isinstance(item, str):
            item = Block(item)
        self.blocks.append(item)
        return self

    @property
    def user(self) -> str:
        if not self.blocks:
            return ""
        parts = [str(block) for block in self.blocks]
        return "\n\n".join(parts)

    def to_text(self) -> str:
        parts = []
        if self.system:
            parts.append(f"System:\n{self.system}")
        if self.user:
            parts.append(f"User:\n{self.user}")
        return "\n\n".join(parts)

    def get_images(self) -> List["Image"]:
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
        return self.to_text()
