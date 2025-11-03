"""Google Gemini LLM implementation."""

from typing import Optional, List, Any
import google.generativeai as genai
from ....llm import LLM, Context


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

    def _build_content(self, context: Context) -> List[Any] | str:
        """Build content for Gemini API, supporting both text and images.

        Returns:
            List of content parts if images are present, otherwise plain string
        """
        has_images = any(block.image for block in context.blocks)

        # Combine system and user prompts for Gemini
        # Gemini doesn't have separate system/user roles like OpenAI
        combined_text = f"{context.system}\n\n{context.user}"

        if not has_images:
            # Text-only: return simple string
            return combined_text

        # Multimodal: build content array
        # Gemini uses PIL Images, so we need to convert from bytes
        from PIL import Image as PILImage
        import io

        content = []

        # Add combined text first
        content.append(combined_text)

        # Add images from blocks
        for block in context.blocks:
            if block.image:
                # Convert image bytes to PIL Image
                image_bytes = block.image.to_bytes()
                pil_image = PILImage.open(io.BytesIO(image_bytes))
                content.append(pil_image)

        return content

    async def generate(self, context: Context, use_json: bool = False) -> str:
        """
        Generate text using Gemini API.

        Supports multimodal content (text + images) and JSON mode.

        Args:
            context: Context object with system, blocks (text + images), etc.
            use_json: If True, force JSON output

        Returns:
            Generated text response from Gemini
        """
        self.logger.info(
            f"Calling Gemini API - model: {self.model_name}, temperature: {self.temperature}, "
            f"json_mode: {use_json}"
        )

        # Build content (may include images)
        content = self._build_content(context)

        # Use JSON mode if requested
        if use_json:
            generation_config = genai.GenerationConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
            )
            response = await self.model.generate_content_async(
                content, generation_config=generation_config
            )
        else:
            response = await self.model.generate_content_async(content)

        # Log token usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            self.logger.info(
                f"Gemini API response - "
                f"prompt_tokens: {response.usage_metadata.prompt_token_count}, "
                f"completion_tokens: {response.usage_metadata.candidates_token_count}, "
                f"total_tokens: {response.usage_metadata.total_token_count}"
            )

        return response.text
