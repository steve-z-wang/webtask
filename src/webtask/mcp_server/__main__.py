"""MCP server entry point."""

import asyncio
import logging

from .server import main

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    asyncio.run(main())
