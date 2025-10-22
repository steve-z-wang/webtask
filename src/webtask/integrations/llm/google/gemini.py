"""Google Gemini LLM implementation."""

from typing import Optional
import google.generativeai as genai
from ....llm import LLM, Tokenizer

# Model max token limits
MODEL_MAX_TOKENS = {
    "gemini-pro": 32768,
    "gemini-1.5-pro": 2097152,  # 2M tokens
    "gemini-1.5-flash": 1048576,  # 1M tokens
    "gemini-2.0-flash": 1048576,  # 1M tokens
    "gemini-2.5-flash": 1048576,  # 1M tokens
}


class GeminiLLM(LLM):
    """
    Google Gemini implementation of LLM.

    Wraps Google's Gemini API for text generation.
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        max_tokens: int,
        model: genai.GenerativeModel,
        model_name: str,
        temperature: float,
    ):
        """
        Initialize GeminiLLM (use create factory instead).

        Args:
            tokenizer: Tokenizer for counting tokens
            max_tokens: Maximum token limit for prompts
            model: Gemini GenerativeModel instance
            model_name: Model name
            temperature: Temperature for generation
        """
        super().__init__(tokenizer, max_tokens)
        self.model_name = model_name
        self.temperature = temperature
        self.model = model

    @classmethod
    def create(
        cls,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> 'GeminiLLM':
        """
        Create a GeminiLLM instance with automatic tokenizer and max_tokens detection.

        Args:
            model: Model name (e.g., "gemini-2.5-flash", "gemini-1.5-pro")
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)
            max_tokens: Override max tokens (if None, auto-detect from model)

        Returns:
            GeminiLLM instance

        Example:
            >>> llm = GeminiLLM.create(model="gemini-2.5-flash")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        # Auto-create tokenizer for this model
        from .gemini_tokenizer import GeminiTokenizer
        tokenizer = GeminiTokenizer(model)

        # Auto-detect max_tokens if not provided
        if max_tokens is None:
            max_tokens = MODEL_MAX_TOKENS.get(model)
            if max_tokens is None:
                raise ValueError(f"Unknown model: {model}. Please specify max_tokens manually.")

        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)

        # Create model with generation config
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            )
        )

        return cls(tokenizer, max_tokens, gemini_model, model, temperature)

    async def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Internal method for actual text generation using Gemini API.

        Args:
            system_prompt: System prompt that sets LLM behavior/role
            user_prompt: User prompt with the actual query/task

        Returns:
            Generated text response from Gemini
        """
        self.logger.info(f"Calling Gemini API - model: {self.model_name}, temperature: {self.temperature}")

        # Combine system and user prompts for Gemini
        # Gemini doesn't have separate system/user roles like OpenAI
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = await self.model.generate_content_async(combined_prompt)

        # Log token usage if available
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            self.logger.info(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        return response.text
