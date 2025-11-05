
# webtask

[![PyPI version](https://badge.fury.io/py/pywebtask.svg)](https://badge.fury.io/py/pywebtask)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered web automation library with autonomous agents and natural language selectors.


## Quick Example

```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

# Create Webtask manager
wt = Webtask()

# Choose your LLM
llm = GeminiLLM.create(model="gemini-2.5-flash")

# Create agent
agent = await wt.create_agent(llm=llm)

# Execute task
result = await agent.execute("search for cats and click the first result")
print(f"Completed: {result.completed}")
```

No CSS selectors. No XPath. Just describe what you want.


## Key Features

- **Three interaction modes**: Autonomous, step-by-step, or imperative control
- **Multimodal understanding**: Visual (screenshots) + text (DOM) context
- **Natural language selectors**: "search box" instead of `#search-input`
- **Built on Playwright**: Reliable, modern browser automation
- **Multiple LLM support**: OpenAI GPT-4 Vision and Google Gemini 2.5


## Status

🚧 Work in progress

Core implementation complete. See [Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks) for evaluation framework.

