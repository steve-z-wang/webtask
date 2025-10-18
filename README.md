# webtask

**Give it a task. It does the work.**

A lightweight DOM-based web agent that executes web tasks from natural language descriptions.

Built on three core technologies:
- **[Playwright](https://playwright.dev/)** - Browser automation
- **[domcontext](https://github.com/steve-z-wang/domcontext)** - Clean DOM context for LLMs
- **[natural-selector](https://github.com/steve-z-wang/natural-selector)** - Natural language element selection

> **⚠️ Early Development:** This is a work in progress. More documentation coming soon.

---

## Quick Start

```python
from webtask import WebAgent

agent = WebAgent()

# That's it. Just describe what you want.
await agent.run(
    url="https://www.google.com",
    task="Search for 'Python web automation' and click the first result"
)
```

---

## How It Works

1. **You describe the task** - In plain English
2. **Agent figures it out** - Uses LLM to understand what to do
3. **Executes autonomously** - Clicks, types, navigates automatically
4. **Returns results** - Success/failure and any extracted data

No complex APIs. No step-by-step instructions. Just describe what you want.

---

## Examples

```python
# Search and extract
await agent.run(
    url="https://wikipedia.org",
    task="Search for 'machine learning' and get the first paragraph"
)

# Fill forms
await agent.run(
    url="https://example.com/contact",
    task="Fill out the form with name 'John' and email 'john@example.com', then submit"
)

# Multi-step tasks
await agent.run(
    url="https://news.ycombinator.com",
    task="Find the top post, open it, read it, and summarize"
)
```

---

## Installation

```bash
pip install webtask[playwright]
playwright install chromium
```

---

## Built With

- **[domcontext](https://github.com/steve-z-wang/domcontext)** - Clean DOM context for LLMs
- **[natural-selector](https://github.com/steve-z-wang/natural-selector)** - Natural language element selection
- **[Playwright](https://playwright.dev/)** - Browser automation

---

## Status

🚧 **Under Active Development**

Current focus:
- Core agent loop implementation
- Task planning and execution
- Error handling and recovery
- Evaluation on Mind2Web dataset

More documentation, examples, and features coming soon.

---

## License

MIT

---

## Related Projects

- [domcontext](https://github.com/steve-z-wang/domcontext) - Parse DOM into LLM-friendly context
- [natural-selector](https://github.com/steve-z-wang/natural-selector) - Select elements with natural language
