"""Close agent tool for MCP server."""

from typing import Any, Dict


async def close_agent_tool(session_manager, session_id: str) -> Dict[str, Any]:
    """
    Close an agent session and clean up resources.

    Args:
        session_manager: SessionManager instance
        session_id: Session ID to close

    Returns:
        Closure status
    """
    # Get agent and playwright from session
    session_data = session_manager.get_session_data(session_id)
    if session_data is None:
        return {
            "success": False,
            "error": "Invalid session ID",
            "message": f"Session {session_id} not found.",
        }

    agent, playwright = session_data

    try:
        # Close agent (closes context/tab)
        await agent.close()

        # Stop playwright instance
        if playwright:
            await playwright.stop()

        # Remove session
        session_manager.close_session(session_id)

        return {
            "success": True,
            "message": f"✅ Session {session_id} closed successfully. Chrome remains running.",
        }

    except Exception as e:
        # Try to remove session even if close failed
        session_manager.close_session(session_id)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to close agent cleanly: {e}. Session removed anyway.",
        }
