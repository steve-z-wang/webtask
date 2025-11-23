---
hide:
  - navigation
  - toc
---

# webtask

[![PyPI version](https://img.shields.io/pypi/v/pywebtask.svg)](https://pypi.org/project/pywebtask/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://steve-z-wang.github.io/webtask/)

Easy to use LLM-powered web automation.

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

- **Simple or complex tasks** - Single actions or multi-step workflows
- **Stateful agents** - Remembers context across tasks
- **Three modes** - Text (DOM), visual (screenshots), or full (both)
- **Verification** - Natural language assertions
- **Structured output** - Extract data with Pydantic schemas
- **Easy integration** - Works with existing browsers

## Get Started

- [Installation & Getting Started](getting-started.md)
- [Examples](examples.md)
- [API Reference](api/index.md)
- [MCP Server](mcp-server.md)
