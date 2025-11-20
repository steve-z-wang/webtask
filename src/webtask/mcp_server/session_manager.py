"""Session manager for MCP server."""

import uuid
from typing import Dict, Optional, Tuple, Any
from webtask import Agent


class SessionManager:
    """Manages agent sessions for MCP server."""

    def __init__(self):
        # Store both agent and playwright instance
        self.sessions: Dict[str, Tuple[Agent, Any]] = {}

    def create_session(self, agent: Agent, playwright: Any = None) -> str:
        """Create a new session with an agent and optional playwright instance."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = (agent, playwright)
        return session_id

    def get_session(self, session_id: str) -> Optional[Agent]:
        """Get agent by session ID."""
        session = self.sessions.get(session_id)
        if session:
            return session[0]  # Return agent
        return None

    def get_session_data(self, session_id: str) -> Optional[Tuple[Agent, Any]]:
        """Get both agent and playwright instance by session ID."""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        """Close and remove a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        return list(self.sessions.keys())
