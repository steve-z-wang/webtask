"""Context class for LLM prompts."""

from typing import List, Union


class Context:
    """
    LLM context with system and user prompts.

    Allows incremental building of user prompt while maintaining system prompt.
    """

    def __init__(self, system: str = ""):
        """
        Create a Context with system prompt.

        Args:
            system: System prompt text
        """
        self.system = system
        self.user = ""

    def append(self, item: Union['Context', str]) -> 'Context':
        """
        Append to user prompt.

        Args:
            item: Context object or string to append

        Returns:
            Self for chaining
        """
        if isinstance(item, Context):
            text = item.user
        else:
            text = str(item)

        if self.user:
            self.user += "\n\n" + text
        else:
            self.user = text

        return self

    @staticmethod
    def combine(items: List[Union['Context', str]]) -> str:
        """
        Combine multiple contexts/strings into single text.

        Args:
            items: List of Context objects or strings

        Returns:
            Combined text string
        """
        texts = []
        for item in items:
            if isinstance(item, Context):
                texts.append(item.user)
            else:
                texts.append(str(item))
        return "\n\n".join(texts)

    def __str__(self) -> str:
        """
        Get user prompt as string.

        Returns:
            User prompt text
        """
        return self.user
