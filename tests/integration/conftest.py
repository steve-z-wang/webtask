"""Pytest configuration for integration tests."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env.test at the start of integration tests
env_test_path = Path(__file__).parent.parent.parent / ".env.test"
load_dotenv(env_test_path)
