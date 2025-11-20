"""Start agent tool for MCP server."""

from typing import Any, Dict
from webtask import Webtask
from playwright.async_api import async_playwright


async def start_agent_tool(session_manager) -> Dict[str, Any]:
    """
    Start a new browser agent session.

    Args:
        session_manager: SessionManager instance

    Returns:
        Session ID and status
    """
    import os
    import subprocess
    import time
    import socket
    from ..config import load_config

    try:
        # Load configuration
        config = load_config()
        llm_config = config.get("llm", {})
        llm_provider = llm_config.get("provider", "gemini")
        browser_config = config.get("browser", {})
        chrome_path = browser_config["chrome_path"]
        debug_port = browser_config["debug_port"]
        data_dir = browser_config["data_dir"]

        # Create LLM based on provider
        if llm_provider == "gemini":
            from webtask.integrations.llm import Gemini

            gemini_config = llm_config.get("gemini", {})
            api_key = gemini_config.get("api_key")
            if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
                return {
                    "success": False,
                    "error": "Gemini API key not configured",
                    "message": "Please edit ~/.config/webtask/config.json and set llm.gemini.api_key",
                }
            llm = Gemini(api_key=api_key)

        elif llm_provider == "bedrock":
            from webtask.integrations.llm import Bedrock

            bedrock_config = llm_config.get("bedrock", {})
            region = bedrock_config.get("region", "us-east-1")
            bearer_token = bedrock_config.get("bearer_token", "")

            # Use bearer token if provided, otherwise use AWS credentials
            if bearer_token:
                llm = Bedrock(region_name=region, bearer_token=bearer_token)
            else:
                llm = Bedrock(region_name=region)

        else:
            return {
                "success": False,
                "error": f"Unknown LLM provider: {llm_provider}",
                "message": "llm.provider must be 'gemini' or 'bedrock'",
            }

        # Check if Chrome is already running on the debug port
        def is_port_open(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            return result == 0

        # Launch Chrome if not running
        if not is_port_open(debug_port):
            # Build Chrome launch command
            cmd = [
                chrome_path,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={data_dir}",
            ]

            # Launch Chrome in background
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for Chrome to start
            for _ in range(30):  # Wait up to 3 seconds
                if is_port_open(debug_port):
                    break
                time.sleep(0.1)
            else:
                return {
                    "success": False,
                    "error": "Chrome startup timeout",
                    "message": f"Chrome did not start on port {debug_port} within 3 seconds",
                }

        # Connect to Chrome via CDP
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(
            f"http://localhost:{debug_port}"
        )

        # Create agent with browser
        wt = Webtask()
        agent = await wt.create_agent_with_browser(llm=llm, browser=browser)

        # Create session with playwright for cleanup
        session_id = session_manager.create_session(agent, playwright)

        return {
            "success": True,
            "session_id": session_id,
            "message": f"✅ Agent started with session ID: {session_id}",
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Configuration not found. Please run onboard tool first.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to start agent: {e}",
        }
