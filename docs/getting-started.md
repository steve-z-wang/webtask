# Getting Started

## Installation

```bash
pip install pywebtask
playwright install chromium
```

## First Task

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import Gemini

async def main():
    wt = Webtask()
    agent = await wt.create_agent(
        llm=Gemini(model="gemini-2.5-flash"),
        wait_after_action=1.0,  # Adjust for slower sites
    )

    await agent.goto("https://practicesoftwaretesting.com")
    await agent.wait(3)

    await agent.do("add 2 Flat-Head Wood Screws to the cart")

    verdict = await agent.verify("the cart contains 2 items")
    if verdict:
        print("Success!")

    await wt.close()

asyncio.run(main())
```

## Configuration

### Two Modes

```python
agent = await wt.create_agent(llm=llm, mode="dom")     # Element IDs (default)
agent = await wt.create_agent(llm=llm, mode="pixel")   # Screen coordinates
```

### Headless Mode

```python
agent = await wt.create_agent(llm=llm, headless=False)  # Show browser (default)
agent = await wt.create_agent(llm=llm, headless=True)   # Hide browser
```

### Stateful Agents

```python
# Agent remembers context across tasks by default
await agent.do("Add 2 screws to the cart")
await agent.do("Add 5 more screws")  # Remembers previous actions
await agent.do("Go to cart")

agent.clear_history()  # Start fresh when needed
```

### Timing Control

!!! warning "Important for Single Page Applications (SPAs)"
    Modern websites often use SPAs where clicking a link changes content without a full page reload. The default `wait_after_action=1.0` second may not be enough for the new content to load, causing the agent to see stale DOM content and make incorrect decisions.

    **Recommendation**: For SPAs, increase `wait_after_action` to 2-3 seconds or use explicit waits.

```python
# Set default wait time for agent (default: 1.0s)
# Increase for SPAs or slow-loading sites
agent = await wt.create_agent(llm=llm, wait_after_action=3.0)

# Override per task
await agent.do("Click submit", wait_after_action=5.0)

# Explicit waits
await agent.wait(3)                  # Simple wait (seconds)
await agent.wait_for_load()          # Wait for page load event
await agent.wait_for_network_idle()  # Wait for network idle (best for SPAs)
```

## Next Steps

- [Examples](examples.md) - See more usage examples
- [API Reference](api/index.md) - Full API documentation
