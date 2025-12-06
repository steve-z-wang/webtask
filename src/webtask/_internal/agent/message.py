"""Agent-specific content types with lifespan for context management."""

from typing import Optional
from webtask.llm.message import Content, Text, Image


class AgentContent(Content):
    """Base content with lifespan for agent context management.

    lifespan controls how many messages this content should be kept:
    - None: keep forever (no purging)
    - 1: keep only in the most recent message
    - 2: keep in the last 2 messages
    - etc.
    """

    lifespan: Optional[int] = None


class AgentText(Text, AgentContent):
    """Text content with lifespan support."""

    pass


class AgentImage(Image, AgentContent):
    """Image content with lifespan support."""

    pass
