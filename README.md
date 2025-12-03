# webtask

[![PyPI version](https://img.shields.io/pypi/v/pywebtask.svg)](https://pypi.org/project/pywebtask/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://steve-z-wang.github.io/webtask/)

Easy-to-use LLM-powered web automation.

## Installation

```bash
pip install pywebtask
playwright install chromium
```

## Quick Start

```python
from webtask import Webtask
from webtask.integrations.llm import GeminiComputerUse

wt = Webtask()
agent = await wt.create_agent(llm=GeminiComputerUse(), mode="visual")

await agent.do("Go to practicesoftwaretesting.com and add 2 Flat-Head Wood Screws to the cart")

verdict = await agent.verify("the cart contains 2 items")
if verdict:
    print("Success!")
```

## Features

**Simple or complex tasks**

```python
await agent.do("Click the login button")                            # Single action
await agent.do("Find the blue shirt, add to cart, and checkout")    # Multi-step task
```

**Stateful agents**

```python
# Agent remembers context across tasks
await agent.do("Add 2 wood screws to cart")
await agent.do("Add 5 cross-head screws")
await agent.do("Go to cart and verify")

agent.clear_history()  # Start fresh
```

**Two modes**

```python
agent = await wt.create_agent(llm=llm, mode="dom")     # Element IDs (default)
agent = await wt.create_agent(llm=llm, mode="pixel")   # Screen coordinates
```

**Verification**

```python
verdict = await agent.verify("the cart contains 7 items")
if verdict:
    print("Success!")
```

**Data extraction**

```python
class ProductInfo(BaseModel):
    name: str
    price: float

product = await agent.extract("product information", ProductInfo)
```

**Error handling**

```python
try:
    await agent.do("Add item to cart")
except TaskAbortedError as e:
    print(f"Task failed: {e}")
```

**Easy integration**

```python
agent = await wt.create_agent(llm=llm)                                  # New browser
agent = await wt.create_agent_with_browser(llm=llm, browser=browser)    # Existing browser
agent = wt.create_agent_with_context(llm=llm, context=context)          # Existing context
agent = wt.create_agent_with_page(llm=llm, page=page)                   # Existing page
```

**Timing control**

```python
# Set default wait time for agent
agent = await wt.create_agent(llm=llm, wait_after_action=2.0)

# Override per task
await agent.do("Click submit", wait_after_action=3.0)

# Explicit waits
await agent.wait_for_load()          # Wait for page load
await agent.wait_for_network_idle()  # Wait for network idle
```

## Supported LLMs

```python
from webtask.integrations.llm import Gemini, GeminiComputerUse, Bedrock

Gemini(model="gemini-2.5-flash")                                # 2.5 Flash
GeminiComputerUse(model="gemini-2.5-computer-use-preview")      # Visual mode
Bedrock(model="anthropic.claude-sonnet-4-20250514-v1:0")        # Claude 4 Sonnet (WIP)
```

## Links

- [Documentation](https://steve-z-wang.github.io/webtask/)
- [Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)

## License

MIT
