"""LLM base class for text generation."""

import logging
from abc import ABC, abstractmethod
from .context import Context


class LLM(ABC):
    """Abstract base class for Large Language Models."""

    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.

        Each LLM provider implements this using their specific tokenization.

        Args:
            text: Text to tokenize and count

        Returns:
            Number of tokens in the text
        """
        pass

    def _check_token_limit(self, context: Context) -> int:
        system_tokens = self.count_tokens(context.system)
        user_tokens = self.count_tokens(context.user)
        total_tokens = system_tokens + user_tokens

        if total_tokens > self.max_tokens:
            raise ValueError(
                f"Token count {total_tokens} exceeds max {self.max_tokens} "
                f"(system: {system_tokens}, user: {user_tokens})"
            )

        return total_tokens

    async def generate(self, context: Context, use_json: bool = False) -> str:
        """Generate text response from context.

        This is a wrapper that handles token checking, then delegates to _generate().

        Args:
            context: Full Context object with system, blocks (text + images), etc.
            use_json: If True, force LLM to return valid JSON (provider-specific)

        Returns:
            Generated text response (always str). If use_json=True, guaranteed to be valid JSON.
        """
        total_tokens = self._check_token_limit(context)
        self.logger.debug(f"LLM API call - Total tokens: {total_tokens}")
        response = await self._generate(context, use_json=use_json)

        return response

    @abstractmethod
    async def _generate(self, context: Context, use_json: bool = False) -> str:
        """Subclasses implement actual LLM call.

        Args:
            context: Full Context object with system, blocks (text + images), etc.
            use_json: If True, force LLM to return valid JSON

        Returns:
            Generated text response
        """
        pass
