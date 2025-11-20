---
hide:
  - navigation
---

# webtask

[![PyPI version](https://badge.fury.io/py/pywebtask.svg)](https://badge.fury.io/py/pywebtask)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered web automation library with autonomous agents.


## Quick Example

```python
from webtask import Webtask
from webtask.integrations.llm import Gemini

# Create Webtask manager
wt = Webtask()

# Choose your LLM
llm = Gemini(model="gemini-2.5-flash")

# Create agent
agent = await wt.create_agent(llm=llm)

# Execute task
result = await agent.do("search for cats and click the first result")
print(f"Status: {result.status}")
```


## Key Features

- **Autonomous agents**: Give it a task, let it figure out the steps
- **Multimodal understanding**: Visual (screenshots) + text (DOM) context
- **Extensible**: Pluggable LLM and browser interfaces - use provided implementations or bring your own
- **Batteries included**: Ships with Gemini LLM and Playwright browser
- **Stateful mode**: Maintain conversation history across multiple tasks


## Status

🚧 Work in progress

Core implementation complete. See [Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks) for evaluation framework.

