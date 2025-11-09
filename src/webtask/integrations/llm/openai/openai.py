"""OpenAI LLM implementation."""

from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from ....llm import LLM, Content, Text, Image


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

    async def generate(
        self, system: str, content: List[Content], use_json: bool = False
    ) -> str:
        """
        Generate text using OpenAI API.

        Supports multimodal content (text + images) and JSON mode.

        Args:
            system: System prompt
            content: Ordered list of Text/Image content parts
            use_json: If True, force JSON output

        Returns:
            Generated text response from OpenAI
        """
        # Build user content from Text/Image parts
        has_images = any(isinstance(part, Image) for part in content)

        if not has_images:
            # Text-only: join all text parts
            user_content = "\n\n".join(
                part.text for part in content if isinstance(part, Text)
            )
        else:
            # Multimodal: build content array
            user_content = []
            for part in content:
                if isinstance(part, Text):
                    user_content.append({"type": "text", "text": part.text})
                elif isinstance(part, Image):
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{part.mime_type.value};base64,{part.data}"
                            },
                        }
                    )

        self.logger.debug(
            f"Calling OpenAI API - model: {self.model}, temperature: {self.temperature}, "
            f"json_mode: {use_json}"
        )

        # Build API call kwargs
        api_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
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
            self.logger.debug(
                f"OpenAI API response - "
                f"prompt_tokens: {response.usage.prompt_tokens}, "
                f"completion_tokens: {response.usage.completion_tokens}, "
                f"total_tokens: {response.usage.total_tokens}"
            )

        return response.choices[0].message.content
