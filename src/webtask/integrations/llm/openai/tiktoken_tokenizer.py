"""TikToken-based tokenizer for OpenAI models."""

import tiktoken
from ....llm import Tokenizer


class TikTokenizer(Tokenizer):
    """
    Tokenizer using tiktoken for OpenAI models.

    Uses tiktoken library to count tokens accurately for OpenAI models.
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize tokenizer.

        Args:
            encoding_name: Tiktoken encoding name
                - "cl100k_base": GPT-4, GPT-3.5-turbo, GPT-4-turbo
                - "p50k_base": Codex models
                - "r50k_base": GPT-3 models (davinci, curie, etc.)
        """
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.encoding_name = encoding_name

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to tokenize and count

        Returns:
            Number of tokens in the text
        """
        return len(self.encoding.encode(text))

    @classmethod
    def for_model(cls, model: str) -> 'TikTokenizer':
        """
        Create tokenizer for specific model.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            TikTokenizer instance configured for the model

        Example:
            >>> tokenizer = TikTokenizer.for_model("gpt-4")
            >>> tokenizer.count_tokens("Hello, world!")
            4
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return cls(encoding.name)
        except KeyError:
            # Default to cl100k_base for unknown models (GPT-4 encoding)
            return cls("cl100k_base")
