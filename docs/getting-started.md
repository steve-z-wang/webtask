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
from webtask.integrations.llm import GeminiComputerUse

async def main():
    wt = Webtask()
    agent = await wt.create_agent(llm=GeminiComputerUse(), mode="visual")

    await agent.do("Go to practicesoftwaretesting.com and add 2 Flat-Head Wood Screws to the cart")

    verdict = await agent.verify("the cart contains 2 items")
    if verdict:
        print("Success!")

    await wt.close()

asyncio.run(main())
```

## Configuration

### Three Modes

```python
agent = await wt.create_agent(llm=llm, mode="text")     # DOM-based (default)
agent = await wt.create_agent(llm=llm, mode="visual")   # Screenshots
agent = await wt.create_agent(llm=llm, mode="full")     # Both
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

```python
# Set default wait time for agent (default: 1.0s)
agent = await wt.create_agent(llm=llm, wait_after_action=2.0)

# Override per task
await agent.do("Click submit", wait_after_action=3.0)

# Explicit waits for SPAs
await agent.wait_for_load()          # Wait for page load
await agent.wait_for_network_idle()  # Wait for network idle
```

## Next Steps

- [Examples](examples.md) - See more usage examples
- [API Reference](api/index.md) - Full API documentation
