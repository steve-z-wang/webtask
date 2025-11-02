"""OpenAI LLM implementation."""

from typing import Optional, List, Dict, Any
import tiktoken
from openai import AsyncOpenAI
from ....llm import LLM, Context

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
        max_tokens: int,
        client: AsyncOpenAI,
        model: str,
        temperature: float,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize OpenAILLM (use create factory instead).

        Args:
            max_tokens: Maximum token limit for prompts
            client: AsyncOpenAI client instance
            model: Model name
            temperature: Temperature for generation
            encoding_name: Tiktoken encoding name
        """
        super().__init__(max_tokens)
        self.model = model
        self.temperature = temperature
        self.client = client
        self.encoding = tiktoken.get_encoding(encoding_name)

    @classmethod
    def create(
        cls,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
    ) -> "OpenAILLM":
        """
        Create an OpenAILLM instance with automatic encoding and max_tokens detection.

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
        # Get encoding for model
        try:
            encoding = tiktoken.encoding_for_model(model)
            encoding_name = encoding.name
        except KeyError:
            # Default to cl100k_base for unknown models (GPT-4 encoding)
            encoding_name = "cl100k_base"

        # Auto-detect max_tokens if not provided
        if max_tokens is None:
            max_tokens = MODEL_MAX_TOKENS.get(model)
            if max_tokens is None:
                raise ValueError(
                    f"Unknown model: {model}. Please specify max_tokens manually."
                )

        client = AsyncOpenAI(api_key=api_key)

        return cls(max_tokens, client, model, temperature, encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to tokenize and count

        Returns:
            Number of tokens in the text
        """
        return len(self.encoding.encode(text))

    def _build_user_content(self, context: Context) -> List[Dict[str, Any]] | str:
        """Build user message content, supporting both text and images.

        Returns:
            List of content blocks if images are present, otherwise plain string
        """
        has_images = any(block.image for block in context.blocks)

        if not has_images:
            # Text-only: return simple string
            return context.user

        # Multimodal: build content array
        content = []
        for block in context.blocks:
            if block.text:
                content.append({"type": "text", "text": block.text})

            if block.image:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": block.image.to_data_url()},
                    }
                )

        return content

    async def _generate(self, context: Context, use_json: bool = False) -> str:
        """
        Internal method for actual text generation using OpenAI API.

        Supports multimodal content (text + images) and JSON mode.

        Args:
            context: Context object with system, blocks (text + images), etc.
            use_json: If True, force JSON output

        Returns:
            Generated text response from OpenAI
        """
        # Build user content (may include images)
        user_content = self._build_user_content(context)

        self.logger.info(
            f"Calling OpenAI API - model: {self.model}, temperature: {self.temperature}, "
            f"json_mode: {use_json}"
        )

        # Build API call kwargs
        api_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": context.system},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.temperature,
        }

        # Add JSON mode if requested
        if use_json:
            api_kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**api_kwargs)

        # Log token usage if available
        if response.usage:
            self.logger.info(
                f"OpenAI API response - "
                f"prompt_tokens: {response.usage.prompt_tokens}, "
                f"completion_tokens: {response.usage.completion_tokens}, "
                f"total_tokens: {response.usage.total_tokens}"
            )

        return response.choices[0].message.content
