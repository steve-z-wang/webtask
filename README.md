# webtask

[![PyPI version](https://img.shields.io/pypi/v/pywebtask.svg)](https://pypi.org/project/pywebtask/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://steve-z-wang.github.io/webtask/)

Easy to use LLM-powered web automation.

## Installation

```bash
pip install pywebtask
playwright install chromium
```

## Quick Start

```python
from webtask import Webtask
from webtask.integrations.llm import Gemini
import os

wt = Webtask()

llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
agent = await wt.create_agent(llm=llm)

await agent.goto("practicesoftwaretesting.com")

await agent.do("Add 2 Flat-Head Wood Screws to the cart")

verdict = await agent.verify("the cart contains 2 items")
if verdict:
    print("Success!")
```

## Features

**Simple or complex tasks** - From single actions to multi-step workflows:

```python
# Simple action
await agent.do("Click the login button")

# Complex multi-step task
await agent.do("Go to the product page, find the blue shirt, add it to cart, and proceed to checkout")
```

**Stateful agents** - Remember context across multiple tasks:

```python
await agent.do("Go to practicesoftwaretesting.com and add 2 Flat-Head Wood Screws to the cart")
await agent.do("Add 5 Cross-head screws to the cart")
await agent.do("Go to the cart page and verify the items")
```

**Verification** - Simple boolean checks with natural language:

```python
verdict = await agent.verify("the cart contains 7 items")
if verdict:
    print("Success!")
```

**Data extraction** - Extract information from pages:

```python
# Simple extraction returns string
price = await agent.extract("total price")
print(f"Price: {price}")

# Structured extraction with Pydantic schema
from pydantic import BaseModel

class ProductInfo(BaseModel):
    name: str
    price: float
    in_stock: bool

product = await agent.extract("product information", ProductInfo)
print(f"{product.name}: ${product.price}")
```

**Error handling** - Catch failures gracefully:

```python
from webtask import TaskAbortedError, VerificationAbortedError, ExtractionAbortedError

try:
    await agent.do("Add item to cart")
except TaskAbortedError as e:
    print(f"Task failed: {e}")
```

**Easy integration** - Multiple ways to create agents:

```python
# Create with new browser
agent = await wt.create_agent(llm=llm)

# Use existing browser
agent = await wt.create_agent_with_browser(llm=llm, browser=browser)

# Use existing context
agent = wt.create_agent_with_context(llm=llm, context=context)

# Use existing page
agent = wt.create_agent_with_page(llm=llm, page=page)
```

## TODO

- Unlimited context - Compact conversation history with LLM for extended sessions
- Computer Use model integration - Pixel-based interaction with Claude Computer Use
- Mind2Web benchmark - Evaluation on Mind2Web dataset

## Links

- [Documentation](https://steve-z-wang.github.io/webtask/)
- [Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)
- [MCP Server](https://steve-z-wang.github.io/webtask/mcp/)

## License

MIT
