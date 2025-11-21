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
import os

async def main():
    wt = Webtask()

    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm)

    await agent.goto("practicesoftwaretesting.com")
    await agent.do("Add 2 Flat-Head Wood Screws to the cart")

    verdict = await agent.verify("the cart contains 2 items")
    if verdict:
        print("Success!")

    await wt.close()

asyncio.run(main())
```

## Configuration

### Headless Mode

```python
# Show browser (default)
agent = await wt.create_agent(llm=llm, headless=False)

# Hide browser
agent = await wt.create_agent(llm=llm, headless=True)
```

### Stateful Agents

```python
# Stateful mode (default) - remembers context
agent = await wt.create_agent(llm=llm, stateful=True)

await agent.goto("practicesoftwaretesting.com")
await agent.do("Add 2 screws to the cart")  # Remembers the site
await agent.do("Go to cart")  # Remembers previous actions
```

### Using Bedrock

```python
from webtask.integrations.llm import Bedrock

llm = Bedrock(model="us.anthropic.claude-haiku-4-5-20251001-v1:0", region="us-east-1")
agent = await wt.create_agent(llm=llm)
```

## Next Steps

- [Examples](examples.md) - See more usage examples
- [API Reference](api/index.md) - Full API documentation
