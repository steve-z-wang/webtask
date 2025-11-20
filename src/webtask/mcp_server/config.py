"""Configuration management for MCP server."""

import json
import os
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the config directory path."""
    return Path.home() / ".config" / "webtask"


def get_config_path() -> Path:
    """Get the config file path."""
    return get_config_dir() / "config.json"


def config_exists() -> bool:
    """Check if config file exists."""
    return get_config_path().exists()


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config not found at {config_path}. Please run onboard tool first."
        )

    with open(config_path, "r") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
