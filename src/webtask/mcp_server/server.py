"""MCP server implementation for webtask."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import config_exists, get_config_dir
from .session_manager import SessionManager
from .tools.onboard import onboard_tool
from .tools.start_agent import start_agent_tool
from .tools.do_task import do_task_tool
from .tools.close_agent import close_agent_tool

# Configure logging to file to prevent stdout pollution
log_dir = get_config_dir()
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "mcp_server.log"

# Set up file handler for webtask logs (overwrite each session)
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

webtask_logger = logging.getLogger("webtask")
webtask_logger.setLevel(logging.DEBUG)
webtask_logger.addHandler(file_handler)
webtask_logger.propagate = False

logger = logging.getLogger(__name__)


class WebtaskMCPServer:
    """Webtask MCP Server."""

    def __init__(self):
        self.server = Server("webtask")
        self.session_manager = SessionManager()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools based on configuration state."""
            tools = []

            # Show onboard tool only if config doesn't exist
            if not config_exists():
                tools.append(
                    Tool(
                        name="onboard",
                        description="Set up webtask configuration (Chrome path, debug port, data directory). Creates a config file that you must edit to add your LLM credentials (Gemini API key or AWS Bedrock settings).",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chrome_path": {
                                    "type": "string",
                                    "description": "Path to Chrome executable (auto-detected if not provided)",
                                },
                                "debug_port": {
                                    "type": "integer",
                                    "description": "Chrome debug port (default: 9222)",
                                    "default": 9222,
                                },
                                "data_dir": {
                                    "type": "string",
                                    "description": "Directory for browser data (default: ~/.config/webtask/browser-data)",
                                },
                            },
                        },
                    )
                )

            # Always show main tools
            tools.extend(
                [
                    Tool(
                        name="start_web_agent",
                        description="Start a new browser agent session. Returns a session_id to use with other tools.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                    Tool(
                        name="do_web_task",
                        description="Execute a web automation task in an existing agent session.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Session ID from start_web_agent",
                                },
                                "task": {
                                    "type": "string",
                                    "description": "Task description in natural language",
                                },
                                "max_steps": {
                                    "type": "integer",
                                    "description": "Maximum steps to execute (default: 20)",
                                    "default": 20,
                                },
                            },
                            "required": ["session_id", "task"],
                        },
                    ),
                    Tool(
                        name="close_web_agent",
                        description="Close an agent session and clean up resources.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": "Session ID to close",
                                }
                            },
                            "required": ["session_id"],
                        },
                    ),
                ]
            )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            import json

            try:
                if name == "onboard":
                    result = await onboard_tool(**arguments)
                elif name == "start_web_agent":
                    result = await start_agent_tool(self.session_manager, **arguments)
                elif name == "do_web_task":
                    result = await do_task_tool(self.session_manager, **arguments)
                elif name == "close_web_agent":
                    result = await close_agent_tool(self.session_manager, **arguments)
                else:
                    result = {"success": False, "error": f"Unknown tool: {name}"}

                # Format result as text
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}", exc_info=True)
                error_result = {
                    "success": False,
                    "error": str(e),
                    "message": f"Tool execution failed: {e}",
                }
                return [
                    TextContent(type="text", text=json.dumps(error_result, indent=2))
                ]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point for MCP server."""
    server = WebtaskMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
