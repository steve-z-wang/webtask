"""Agent-specific content and message types with lifespan for context management."""

from typing import List, Optional
from webtask.llm.message import (
    Content,
    TextContent,
    ImageContent,
    ImageMimeType,
    UserMessage,
    ToolResultMessage,
    ToolResult,
)


class AgentContent(Content):
    """Base content with lifespan for agent context management.

    lifespan controls how many messages this content should be kept:
    - None: keep forever (no purging)
    - 1: keep only in the most recent message
    - 2: keep in the last 2 messages
    - etc.
    """

    lifespan: Optional[int] = None


class AgentTextContent(TextContent, AgentContent):
    """Text content with lifespan support."""

    pass


class AgentImageContent(ImageContent, AgentContent):
    """Image content with lifespan support."""

    pass


class AgentUserMessage(UserMessage):
    """User message with agent content that supports lifespan."""

    content: Optional[List[AgentContent]] = None


class AgentToolResultMessage(ToolResultMessage):
    """Tool result message with agent content that supports lifespan."""

    content: Optional[List[AgentContent]] = None
