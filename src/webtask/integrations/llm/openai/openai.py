"""OpenAI LLM implementation."""

from typing import Optional
from openai import AsyncOpenAI
from ....llm import LLM, Tokenizer

# Model max token limits
MODEL_MAX_TOKENS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-4.1": 128000,
    "gpt-4.1-mini": 128000,
    "gpt-5-nano": 400000,
}


class OpenAILLM(LLM):
    """
    OpenAI implementation of LLM.

    Wraps OpenAI's API for text generation (GPT-4, GPT-3.5, etc.).
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        max_tokens: int,
        client: AsyncOpenAI,
        model: str,
        temperature: float,
    ):
        """
        Initialize OpenAILLM (use create factory instead).

        Args:
            tokenizer: Tokenizer for counting tokens
            max_tokens: Maximum token limit for prompts
            client: AsyncOpenAI client instance
            model: Model name
            temperature: Temperature for generation
        """
        super().__init__(tokenizer, max_tokens)
        self.model = model
        self.temperature = temperature
        self.client = client

    @classmethod
    def create(
        cls,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
    ) -> 'OpenAILLM':
        """
        Create an OpenAILLM instance with automatic tokenizer and max_tokens detection.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)
            max_tokens: Override max tokens (if None, auto-detect from model)

        Returns:
            OpenAILLM instance

        Example:
            >>> llm = OpenAILLM.create(model="gpt-4")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        # Auto-create tokenizer for this model
        from .tiktoken_tokenizer import TikTokenizer
        tokenizer = TikTokenizer.for_model(model)

        # Auto-detect max_tokens if not provided
        if max_tokens is None:
            max_tokens = MODEL_MAX_TOKENS.get(model)
            if max_tokens is None:
                raise ValueError(f"Unknown model: {model}. Please specify max_tokens manually.")

        client = AsyncOpenAI(api_key=api_key)

        return cls(tokenizer, max_tokens, client, model, temperature)

    async def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Internal method for actual text generation using OpenAI API.

        Args:
            system_prompt: System prompt that sets LLM behavior/role
            user_prompt: User prompt with the actual query/task

        Returns:
            Generated text response from OpenAI
        """
        self.logger.info(f"Calling OpenAI API - model: {self.model}, temperature: {self.temperature}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
        )

        # Log token usage if available
        if response.usage:
            self.logger.info(
                f"OpenAI API response - "
                f"prompt_tokens: {response.usage.prompt_tokens}, "
                f"completion_tokens: {response.usage.completion_tokens}, "
                f"total_tokens: {response.usage.total_tokens}"
            )

        return response.choices[0].message.content
