"""Pytest configuration for integration tests."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env at the start of integration tests
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
