"""LLM base class for text generation."""

from abc import ABC, abstractmethod
from .tokenizer import Tokenizer
from .context import Context


class LLM(ABC):
    """
    Abstract base class for Large Language Models.

    Concrete implementations (GPT-4, Gemini, etc.) should inherit from this class
    and implement the generate method.
    """

    def __init__(self, tokenizer: Tokenizer, max_tokens: int):
        """
        Initialize the LLM.

        Args:
            tokenizer: Tokenizer for counting tokens
            max_tokens: Maximum token limit for prompts
        """
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    def _check_token_limit(self, context: Context) -> int:
        """
        Check if context exceeds token limit.

        Args:
            context: Context with system and user prompts

        Returns:
            Total token count

        Raises:
            ValueError: If total tokens exceed max_tokens
        """
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
        """
        Generate text based on context.

        Checks token limits before generating.

        Args:
            context: Context with system and user prompts

        Returns:
            Generated text response from the LLM

        Raises:
            ValueError: If token count exceeds max_tokens
        """
        self._check_token_limit(context)
        return await self._generate(context.system, context.user)

    @abstractmethod
    async def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Internal method for actual text generation.

        Subclasses must implement this method to perform the actual LLM call.

        Args:
            system_prompt: System prompt that sets LLM behavior/role
            user_prompt: User prompt with the actual query/task

        Returns:
            Generated text response from the LLM
        """
        pass
