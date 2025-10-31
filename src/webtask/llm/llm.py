"""LLM base class for text generation."""

import logging
from abc import ABC, abstractmethod
from .tokenizer import Tokenizer
from .context import Context


class LLM(ABC):
    """Abstract base class for Large Language Models."""

    def __init__(self, tokenizer: Tokenizer, max_tokens: int):
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)

    def _check_token_limit(self, context: Context) -> int:
        system_tokens = self.tokenizer.count_tokens(context.system)
        user_tokens = self.tokenizer.count_tokens(context.user)
        total_tokens = system_tokens + user_tokens

        if total_tokens > self.max_tokens:
            raise ValueError(
                f"Token count {total_tokens} exceeds max {self.max_tokens} "
                f"(system: {system_tokens}, user: {user_tokens})"
            )

        return total_tokens

    async def generate(self, context: Context) -> str:
        """Generate text based on context."""
        total_tokens = self._check_token_limit(context)
        self.logger.debug(f"LLM API call - Total tokens: {total_tokens}")
        response = await self._generate(context.system, context.user)

        return response

    @abstractmethod
    async def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """Subclasses implement actual LLM call."""
        pass
