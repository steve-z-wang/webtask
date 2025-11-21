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
from webtask.integrations.llm import Gemini
import os

wt = Webtask()

llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
agent = await wt.create_agent(llm=llm)

await agent.goto("https://practicesoftwaretesting.com/")

await agent.do("Add 2 Flat-Head Wood Screws to the cart")

verdict = await agent.verify("the cart contains 2 items")
if verdict:
    print("Success!")
```

## Features

**Simple or complex tasks** - From single actions to multi-step workflows

**Stateful agents** - Remember context across multiple tasks

**Verification** - Simple boolean checks with natural language

**Structured output** - Extract data with Pydantic schemas

**Easy integration** - Multiple ways to create agents

## Get Started

- [Installation & Getting Started](getting-started.md)
- [Examples](examples.md)
- [API Reference](api/index.md)
- [MCP Server](mcp-server.md)
