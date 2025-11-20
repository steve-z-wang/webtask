"""Onboard tool for initial MCP server setup."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict


def find_chrome_executable() -> str:
    """Find Chrome executable path on the system."""
    # Common Chrome paths by platform
    chrome_paths = [
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        # Windows
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]

    # Check common paths
    for path in chrome_paths:
        if os.path.exists(path):
            return path

    # Try which command (Linux/macOS)
    chrome_bin = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome_bin:
        return chrome_bin

    raise FileNotFoundError(
        "Could not find Chrome/Chromium executable. Please install Chrome or provide path manually."
    )


async def onboard_tool(
    chrome_path: str = None, debug_port: int = 9222, data_dir: str = None
) -> Dict[str, Any]:
    """
    Set up webtask MCP server configuration.

    Args:
        chrome_path: Path to Chrome executable (auto-detected if not provided)
        debug_port: Chrome debug port (default: 9222)
        data_dir: Directory for browser data (default: ~/.config/webtask/browser-data)

    Returns:
        Configuration details and setup status
    """
    from ..config import get_config_dir, get_config_path, save_config

    # Auto-detect Chrome if not provided
    if chrome_path is None:
        try:
            chrome_path = find_chrome_executable()
        except FileNotFoundError as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Please provide chrome_path parameter with the path to your Chrome executable.",
            }

    # Verify Chrome executable exists
    if not os.path.exists(chrome_path):
        return {
            "success": False,
            "error": f"Chrome executable not found at: {chrome_path}",
            "message": "Please provide a valid chrome_path.",
        }

    # Set default data directory
    if data_dir is None:
        data_dir = str(get_config_dir() / "browser-data")

    # Create config directory
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create browser data directory
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    # Save configuration with placeholder for LLM settings
    config = {
        "llm": {
            "provider": "gemini",  # "gemini" or "bedrock"
            "gemini": {
                "api_key": "YOUR_GEMINI_API_KEY_HERE",
                "model": "gemini-2.5-flash",  # Optional: override default model
            },
            "bedrock": {
                "region": "us-east-1",
                "bearer_token": "",  # AWS Bedrock API key (leave empty to use environment AWS_BEARER_TOKEN_BEDROCK)
                "model": "us.anthropic.claude-haiku-4-5-20251001-v1:0",  # Optional: override default model
            },
        },
        "browser": {
            "chrome_path": chrome_path,
            "debug_port": debug_port,
            "data_dir": data_dir,
        },
    }
    save_config(config)

    config_path = get_config_path()
    return {
        "success": True,
        "config_path": str(config_path),
        "message": f"""✅ Configuration file created at: {config_path}

⚠️  NEXT STEP: Edit the config file and set your LLM provider:

Option 1 - Gemini (default):
  "llm": {{
    "provider": "gemini",
    "gemini": {{ "api_key": "<your-api-key>" }}
  }}

Option 2 - AWS Bedrock:
  "llm": {{
    "provider": "bedrock",
    "bedrock": {{
      "region": "us-east-1",
      "bearer_token": "<optional-bearer-token>"
    }}
  }}
  (Leave bearer_token empty to use ~/.aws/credentials)

Then run start_agent to begin.""",
    }
