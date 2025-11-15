"""Message filtering utilities for managing LLM conversation history."""

from typing import List, Type, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from webtask.llm import Message


class MessageFilter:
    """Filter messages by type to manage conversation history."""

    def __init__(
        self,
        include_types: Set[Type["Message"]] | None = None,
        exclude_types: Set[Type["Message"]] | None = None,
    ):
        """Initialize message filter.

        Args:
            include_types: Only keep messages of these types (if specified)
            exclude_types: Remove messages of these types (if specified)

        Note: If both are specified, include_types takes precedence.
        """
        self.include_types = include_types
        self.exclude_types = exclude_types

    def filter(self, messages: List["Message"]) -> List["Message"]:
        """Filter messages by type.

        Args:
            messages: List of messages to filter

        Returns:
            Filtered list of messages
        """
        if self.include_types is not None:
            # Keep only messages of included types
            return [msg for msg in messages if type(msg) in self.include_types]
        elif self.exclude_types is not None:
            # Remove messages of excluded types
            return [msg for msg in messages if type(msg) not in self.exclude_types]
        else:
            # No filtering
            return messages
