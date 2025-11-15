"""Message purging for sliding window context management."""

from typing import List, Optional, Type
from webtask.llm import Message


def purge_messages_content(
    messages: List[Message],
    by_tags: List[str],
    message_types: Optional[List[Type[Message]]] = None,
    keep_last_messages: int = 2,
) -> List[Message]:
    """Purge old tagged content from message history to keep context bounded.

    Args:
        messages: List of messages to purge
        by_tags: Content tags to purge (e.g., ["observation"])
        message_types: Message types to purge from (e.g., [ToolResultMessage]). If None, purges from all types.
        keep_last_messages: Number of recent messages to keep with full tagged content

    Returns:
        List of messages with old tagged content removed
    """
    if not messages:
        return messages

    def _has_tagged_content(msg: Message) -> bool:
        """Check if message has content with any of the purge tags."""
        if not msg.content:
            return False
        return any(content_item.tag in by_tags for content_item in msg.content)

    def _strip_tagged_content(msg: Message) -> Message:
        """Remove content items with purge tags from message."""
        if not msg.content:
            return msg

        filtered_content = [
            content_item
            for content_item in msg.content
            if content_item.tag not in by_tags
        ]

        return msg.model_copy(
            update={"content": filtered_content if filtered_content else None}
        )

    # Find messages that match type and have tagged content
    tagged_message_indices = []
    for i, msg in enumerate(messages):
        if message_types is not None:
            if not any(isinstance(msg, msg_type) for msg_type in message_types):
                continue

        if _has_tagged_content(msg):
            tagged_message_indices.append(i)

    # Determine cutoff index
    if len(tagged_message_indices) > keep_last_messages:
        cutoff_index = tagged_message_indices[-keep_last_messages]
    else:
        cutoff_index = 0

    # Build purged list
    purged = []
    for i, msg in enumerate(messages):
        if i < cutoff_index and i in tagged_message_indices:
            purged.append(_strip_tagged_content(msg))
        else:
            purged.append(msg)

    return purged
