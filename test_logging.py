"""Test script to demonstrate execution logging."""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def main():
    """Test execution logging with a simple task."""

    print("=" * 80)
    print("Starting webtask execution")
    print("=" * 80)
    print()

    # Import after logging is configured
    from webtask import Webtask
    from webtask.integrations.llm import GeminiLLM

    # Create webtask instance
    wt = Webtask(headless=False)

    # Create LLM
    llm = GeminiLLM.create(model="gemini-2.0-flash-exp")

    # Create agent
    agent = await wt.create_agent(llm=llm, action_delay=1.0)

    # Execute task
    print("Executing task: Search for 'Python web automation' on Google")
    print()

    try:
        result = await agent.execute(
            task_description="Go to google.com and search for 'Python web automation'",
            max_cycles=5
        )

        # Print detailed execution summary
        print(result)

    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        await agent.close()
        await wt.close()


if __name__ == "__main__":
    asyncio.run(main())
