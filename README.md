# webtask

[![PyPI version](https://img.shields.io/pypi/v/pywebtask.svg)](https://pypi.org/project/pywebtask/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/pr.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered web automation with autonomous agents.

**[📚 Documentation](https://steve-z-wang.github.io/webtask/)** | **[🐍 PyPI](https://pypi.org/project/pywebtask/)** | **[📊 Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)**

---

## Quick Start

```bash
pip install pywebtask
playwright install chromium
export GEMINI_API_KEY="your-key"  # or OPENAI_API_KEY
```

**Autonomous mode** - Give it a task, let the agent figure out the steps:
```python
from webtask import Webtask
from webtask.integrations.llm import Gemini
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    llm = Gemini(model="gemini-2.5-flash")

    agent = await Webtask().create_agent_with_browser(llm=llm, browser=browser)

    result = await agent.do("search for cats and click the first result")
```

---

## Features

- **Multimodal by default** - Sees screenshots with bounding boxes + DOM text
- **Extensible** - Pluggable LLM and browser interfaces
- **Batteries included** - OpenAI, Gemini LLMs and Playwright browser provided
- **Isolated sessions** - Separate cookies and storage per agent

---

## Documentation

**[Full Documentation](https://steve-z-wang.github.io/webtask/)**

- [Getting Started](https://steve-z-wang.github.io/webtask/getting-started/)
- [Examples](https://steve-z-wang.github.io/webtask/examples/)
- [API Reference](https://steve-z-wang.github.io/webtask/api/)

---

## Benchmarks

[webtask-benchmarks](https://github.com/steve-z-wang/webtask-benchmarks) - Evaluation on Mind2Web and other benchmarks

---

## License

MIT
