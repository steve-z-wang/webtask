"""LLM base class for text generation."""

import logging
from abc import ABC, abstractmethod
from typing import List
from .content import Content


class LLM(ABC):
    """Abstract base class for Large Language Models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def generate(
        self, system: str, content: List[Content], use_json: bool = False
    ) -> str:
        """Generate text response from system prompt and content.

        Args:
            system: System prompt string
            content: Ordered list of Text/Image content parts
            use_json: If True, force LLM to return valid JSON (provider-specific)

        Returns:
            Generated text response (always str). If use_json=True, guaranteed to be valid JSON.

        Note:
            Token limit checking is handled by the LLM API itself.
            If the prompt exceeds limits, the API will return an error.
        """
        pass
