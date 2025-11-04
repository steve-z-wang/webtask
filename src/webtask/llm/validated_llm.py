"""LLM wrapper that validates responses with automatic retry."""

import json
from typing import TypeVar, Callable
from pydantic import ValidationError
from .llm import LLM
from .context import Context, Block
from ..utils.json_parser import parse_json

T = TypeVar("T")


class ValidatedLLM:
    """
    Wrapper around LLM that validates JSON responses with automatic retry.

    When the LLM produces invalid JSON or validation fails, appends error
    feedback to the context and retries, allowing the LLM to see and fix its mistakes.
    """

    def __init__(self, llm: LLM):
        """
        Create a ValidatedLLM wrapper.

        Args:
            llm: The underlying LLM to wrap
        """
        self.llm = llm

    async def generate_validated(
        self,
        context: Context,
        validator: Callable[[dict], T],
        max_retries: int = 3,
    ) -> T:
        """
        Generate and validate LLM response with automatic retry on errors.

        Args:
            context: Context to send to LLM (will be mutated on retry with error feedback)
            validator: Function that validates parsed JSON dict (e.g., model.validate_python)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Validated response object

        Raises:
            ValueError: If parsing/validation fails after all retries
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Generate JSON response
                response = await self.llm.generate(context, use_json=True)

                # Parse JSON (handles markdown fences)
                cleaned_json_dict = parse_json(response)

                # Validate with provided validator
                return validator(cleaned_json_dict)

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # If not the last attempt, append error feedback to context and retry
                if attempt < max_retries - 1:
                    error_type = type(e).__name__
                    error_msg = str(e)

                    # Append error feedback to END of context
                    feedback = (
                        f"\n❌ ERROR: Your previous JSON response was invalid.\n\n"
                        f"Error type: {error_type}\n"
                        f"Error details: {error_msg}\n\n"
                        f"Please provide a valid JSON response that matches the required schema."
                    )
                    context.append(Block(feedback))
                    # Loop continues with updated context
                else:
                    # Last attempt failed, raise error
                    raise ValueError(
                        f"Failed to parse LLM response after {max_retries} attempts. "
                        f"Last error: {type(e).__name__}: {str(e)}"
                    ) from last_error

        # Should never reach here, but just in case
        raise last_error
