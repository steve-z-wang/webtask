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
# Stateful mode (default) - remembers context
agent = await wt.create_agent(llm=llm, stateful=True)

await agent.do("Add 2 screws to the cart")
await agent.do("Add 5 more screws")  # Remembers previous actions
await agent.do("Go to cart")
```

## Next Steps

- [Examples](examples.md) - See more usage examples
- [API Reference](api/index.md) - Full API documentation
