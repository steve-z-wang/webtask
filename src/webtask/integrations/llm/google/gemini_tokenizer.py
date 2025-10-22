"""Gemini-based tokenizer for Google Gemini models."""

import google.generativeai as genai
from ....llm import Tokenizer


class GeminiTokenizer(Tokenizer):
    """
    Tokenizer using Google Gemini's count_tokens API.

    Uses Gemini's actual tokenization to count tokens accurately.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize tokenizer.

        Args:
            model_name: Gemini model name (e.g., "gemini-2.5-flash", "gemini-1.5-pro")
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's API.

        Args:
            text: Text to tokenize and count

        Returns:
            Number of tokens in the text

        Note:
            This makes an API call to Gemini's count_tokens endpoint.
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            # Fallback to character-based approximation if API fails
            # Rough estimate: ~4 chars per token
            return len(text) // 4
