"""Tokenizer base class for counting tokens."""

from abc import ABC, abstractmethod


class Tokenizer(ABC):
    """
    Abstract base class for tokenizers.

    Tokenizers are used to count tokens in text strings,
    which is important for managing LLM context limits.
    """

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.

        Args:
            text: Text to tokenize and count

        Returns:
            Number of tokens in the text
        """
        pass
