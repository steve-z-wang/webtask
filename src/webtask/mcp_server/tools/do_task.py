"""Do task tool for MCP server."""

from typing import Any, Dict


async def do_task_tool(
    session_manager, session_id: str, task: str, max_steps: int = 20
) -> Dict[str, Any]:
    """
    Execute a task in an existing agent session.

    Args:
        session_manager: SessionManager instance
        session_id: Session ID from start_agent
        task: Task description in natural language
        max_steps: Maximum steps to execute (default: 20)

    Returns:
        Task execution result
    """
    # Get agent from session
    agent = session_manager.get_session(session_id)
    if agent is None:
        return {
            "success": False,
            "error": "Invalid session ID",
            "message": f"Session {session_id} not found. Please start an agent first.",
        }

    try:
        # Execute task
        result = await agent.do(task, max_steps=max_steps)

        return {
            "success": True,
            "status": result.status.value,
            "feedback": result.feedback,
            "output": result.output,
            "message": f"Task completed with status: {result.status.value}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Task execution failed: {e}",
        }
