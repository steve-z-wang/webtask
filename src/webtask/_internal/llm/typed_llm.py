"""TypedLLM - LLM wrapper with automatic JSON parsing and validation."""

from typing import Type, TypeVar
from pydantic import BaseModel
from webtask.llm import LLM, Context
from webtask.utils import parse_json

T = TypeVar("T", bound=BaseModel)


class TypedLLM:
    """LLM wrapper that handles JSON parsing and Pydantic validation."""

    def __init__(self, llm: LLM):
        self._llm = llm

    async def generate(self, context: Context, response_model: Type[T]) -> T:
        """Generate and parse response into Pydantic model.

        Args:
            context: Context to generate from
            response_model: Pydantic model class to validate response

        Returns:
            Validated Pydantic model instance
        """
        response = await self._llm.generate(context, use_json=True)
        response_dict = parse_json(response)
        return response_model.model_validate(response_dict)
