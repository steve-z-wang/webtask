# webtask

[![PyPI version](https://img.shields.io/pypi/v/pywebtask.svg)](https://pypi.org/project/pywebtask/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/test.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered web automation library with autonomous agents and natural language selectors.

**[📚 Documentation](https://steve-z-wang.github.io/webtask/)** | **[🐍 PyPI](https://pypi.org/project/pywebtask/)** | **[📊 Benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)**

---

## What it does

Three ways to use it:

**High-level** - Give it a task, let it figure out the steps
**Step-by-step** - Execute tasks one step at a time for debugging/control
**Low-level** - Tell it exactly what to do with natural language selectors

Uses multimodal LLMs (GPT-4 Vision, Gemini 2.5) to understand pages visually and through DOM. Sends screenshots with bounding boxes by default for better accuracy. Built with Playwright for the browser stuff.

---

## Quick look

**Setup:**
```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

# Create Webtask manager (browser launches lazily)
wt = Webtask()

# Choose your LLM (Gemini or OpenAI)
llm = GeminiLLM.create(model="gemini-2.5-flash")

# Create agent (screenshots with bounding boxes enabled by default)
agent = await wt.create_agent(llm=llm)

# Or disable screenshots for faster/cheaper operation
# agent = await wt.create_agent(llm=llm, use_screenshot=False)
```

**High-level autonomous:**
```python
# Agent figures out the steps
result = await agent.execute("search for cats and click the first result")
print(f"Completed: {result.completed}")
```

**Step-by-step execution:**
```python
# Execute task one step at a time
agent.set_task("add 2 items to cart")

for i in range(10):
    step = await agent.run_step()

    print(f"Step {i+1}: {len(step.proposal.actions)} actions")
    print(f"Status: {step.proposal.message}")

    if step.proposal.complete:
        break

# Useful for debugging, progress tracking, or custom control flow
```

**Low-level imperative:**
```python
# You control the steps, agent handles the selectors
await agent.navigate("https://google.com")

search_box = await agent.select("search box")
await search_box.fill("cats")

button = await agent.select("search button")
await button.click()

# Wait for page to stabilize
await agent.wait_for_idle()

# Take screenshot
await agent.screenshot("result.png")
```

No CSS selectors. No XPath. Just describe what you want.

---

## How it works

**High-level mode** - The agent loop:
1. Proposer looks at the page (text DOM + screenshot with bounding boxes) and task, proposes next actions AND checks if task is complete
2. Executer runs the actions (navigate, click, fill, type)
3. Repeat until task is complete

The agent sees both text (DOM tree with element IDs) and visual context (screenshot with labeled bounding boxes) for more accurate understanding.

**Step-by-step mode** - Same as high-level but you control the loop:
- `agent.set_task(description)` - Set the task
- `agent.run_step()` - Execute one step (propose → execute)
- Setting a new task automatically resets history

**Low-level mode** - You call methods directly:
- `agent.navigate(url)` - Go to a page
- `agent.select(description)` - Find element by natural language
- `element.click()`, `element.fill(text)`, `element.type(text)` - Interact with elements
- `agent.wait(seconds)` - Wait for specific duration
- `agent.wait_for_idle()` - Wait for network/DOM to stabilize
- `agent.screenshot(path)` - Capture page screenshot

All modes use the same core: LLM sees cleaned DOM representation plus screenshots with bounding boxes for accurate understanding. No CSS selectors, no XPath - just natural language.

---

## Installation

```bash
pip install pywebtask
playwright install chromium
```

Set up your API key:
```bash
export GEMINI_API_KEY="your-api-key"  # or OPENAI_API_KEY
```

---

## Documentation

**[📚 Full Documentation](https://steve-z-wang.github.io/webtask/)**

- [Getting Started](https://steve-z-wang.github.io/webtask/getting-started/) - Installation and first steps
- [Examples](https://steve-z-wang.github.io/webtask/examples/) - Complete code examples
- [API Reference](https://steve-z-wang.github.io/webtask/api/) - Detailed API documentation
- [Architecture](https://steve-z-wang.github.io/webtask/architecture/) - How it works internally

---

## Benchmarks

Evaluate webtask on standard web agent benchmarks:

**[webtask-benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)** - Evaluation framework for Mind2Web and other benchmarks

---

## Contributing

See [TODO.md](TODO.md) for planned features and improvements.

Contributions welcome! Open an issue or submit a PR.

---

## License

MIT
