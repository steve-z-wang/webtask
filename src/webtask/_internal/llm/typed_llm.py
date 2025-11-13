
from typing import Type, TypeVar, List, Tuple
from pydantic import BaseModel
from webtask.llm import LLM, Content, Text, Image as ImageContent
from .context import Context
from webtask._internal.utils import parse_json

T = TypeVar("T", bound=BaseModel)


class TypedLLM:

    def __init__(self, llm: LLM):
        self._llm = llm

    def _context_to_llm_input(self, context: Context) -> Tuple[str, List[Content]]:
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
        system, content = self._context_to_llm_input(context)
        response = await self._llm.generate(system, content, use_json=True)
        response_dict = parse_json(response)
        return response_model.model_validate(response_dict)
