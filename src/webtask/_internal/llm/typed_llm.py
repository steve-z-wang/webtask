"""TypedLLM - LLM wrapper with automatic JSON parsing and validation."""

from typing import Type, TypeVar, List, Tuple
from pydantic import BaseModel
from webtask.llm import LLM, Content, Text, Image as ImageContent
from .context import Context
from webtask._internal.utils import parse_json

T = TypeVar("T", bound=BaseModel)


class TypedLLM:
    """LLM wrapper that handles JSON parsing and Pydantic validation."""

    def __init__(self, llm: LLM):
        self._llm = llm

    def _context_to_llm_input(self, context: Context) -> Tuple[str, List[Content]]:
        """
        Convert internal Context to LLM input format (system, content).

        Args:
            context: Internal Context with blocks

        Returns:
            Tuple of (system_prompt, content_list) where content_list is ordered Text/Image parts
        """
        content: List[Content] = []

        def process_block(block):
            # Add text content if present
            text_parts = []
            if block.heading:
                text_parts.append(f"## {block.heading}")
            if block.content:
                text_parts.append(block.content)

            if text_parts:
                content.append(Text(text="\n\n".join(text_parts)))

            # Add image if present
            if block.image:
                content.append(ImageContent(data=block.image.to_base64()))

            # Process nested blocks
            for nested_block in block.blocks:
                process_block(nested_block)

        for block in context.blocks:
            process_block(block)

        return (context.system, content)

    async def generate(self, context: Context, response_model: Type[T]) -> T:
        """Generate and parse response into Pydantic model.

        Args:
            context: Context to generate from
            response_model: Pydantic model class to validate response

        Returns:
            Validated Pydantic model instance
        """
        system, content = self._context_to_llm_input(context)
        response = await self._llm.generate(system, content, use_json=True)
        response_dict = parse_json(response)
        return response_model.model_validate(response_dict)
