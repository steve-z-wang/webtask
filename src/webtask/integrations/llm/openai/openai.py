"""OpenAI LLM implementation."""

from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from ....llm import LLM, Context


class OpenAILLM(LLM):
    """
    OpenAI implementation of LLM.

    Wraps OpenAI's API for text generation (GPT-4, GPT-3.5, etc.).
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        temperature: float,
    ):
        """
        Initialize OpenAILLM (use create factory instead).

        Args:
            client: AsyncOpenAI client instance
            model: Model name
            temperature: Temperature for generation
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.client = client

    @classmethod
    def create(
        cls,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 1,
    ) -> "OpenAILLM":
        """
        Create an OpenAILLM instance.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            OpenAILLM instance

        Example:
            >>> llm = OpenAILLM.create(model="gpt-4")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        client = AsyncOpenAI(api_key=api_key)
        return cls(client, model, temperature)

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

    async def generate(self, context: Context, use_json: bool = False) -> str:
        """
        Generate text using OpenAI API.

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
