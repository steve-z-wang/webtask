"""Google Gemini LLM implementation."""

from typing import Optional, List
import google.generativeai as genai
from ....llm import LLM, Content, Text, Image


class GeminiLLM(LLM):
    """
    Google Gemini implementation of LLM.

    Wraps Google's Gemini API for text generation.
    """

    def __init__(
        self,
        model: genai.GenerativeModel,
        model_name: str,
        temperature: float,
    ):
        """
        Initialize GeminiLLM (use create factory instead).

        Args:
            model: Gemini GenerativeModel instance
            model_name: Model name
            temperature: Temperature for generation
        """
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.model = model

    @classmethod
    def create(
        cls,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> "GeminiLLM":
        """
        Create a GeminiLLM instance.

        Args:
            model: Model name (e.g., "gemini-2.5-flash", "gemini-1.5-pro")
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            GeminiLLM instance

        Example:
            >>> llm = GeminiLLM.create(model="gemini-2.5-flash")
            >>> response = await llm.generate("You are helpful", "Hello!")
        """
        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)

        # Create model with generation config
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            ),
        )

        return cls(gemini_model, model, temperature)

    async def generate(
        self, system: str, content: List[Content], use_json: bool = False
    ) -> str:
        """
        Generate text using Gemini API.

        Supports multimodal content (text + images) and JSON mode.

        Args:
            system: System prompt
            content: Ordered list of Text/Image content parts
            use_json: If True, force JSON output

        Returns:
            Generated text response from Gemini
        """
        self.logger.debug(
            f"Calling Gemini API - model: {self.model_name}, temperature: {self.temperature}, "
            f"json_mode: {use_json}"
        )

        # Build content for Gemini API
        # Gemini doesn't have separate system/user roles, so combine them
        has_images = any(isinstance(part, Image) for part in content)

        if not has_images:
            # Text-only: combine system + all text parts
            text_parts = [system] + [
                part.text for part in content if isinstance(part, Text)
            ]
            gemini_content = "\n\n".join(text_parts)
        else:
            # Multimodal: build content array with PIL Images
            from PIL import Image as PILImage
            import io
            import base64

            gemini_content = []

            # Add system prompt first
            gemini_content.append(system)

            # Add content parts in order
            for part in content:
                if isinstance(part, Text):
                    gemini_content.append(part.text)
                elif isinstance(part, Image):
                    # Convert base64 to PIL Image
                    image_bytes = base64.b64decode(part.data)
                    pil_image = PILImage.open(io.BytesIO(image_bytes))
                    gemini_content.append(pil_image)

        # Use JSON mode if requested
        if use_json:
            generation_config = genai.GenerationConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
            )
            response = await self.model.generate_content_async(
                gemini_content, generation_config=generation_config
            )
        else:
            response = await self.model.generate_content_async(gemini_content)

        # Log token usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.debug(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        return response.text
