# webtask

[![PyPI version](https://badge.fury.io/py/pywebtask.svg)](https://badge.fury.io/py/pywebtask)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/steve-z-wang/webtask/actions/workflows/test.yml/badge.svg)](https://github.com/steve-z-wang/webtask/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered web automation library with autonomous agents and natural language selectors.

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

All modes use the same core: LLM sees cleaned DOM with element IDs like `button-0` instead of raw HTML, plus a screenshot with bounding boxes showing exactly where each element is. Clean input, clean output.

**Available tools for autonomous mode:**
- `navigate(url)` - Navigate to a URL
- `click(element_id)` - Click an element
- `fill(element_id, value)` - Fill form field instantly
- `type(element_id, text)` - Type text character-by-character with realistic delays

---

## Status

🚧 Work in progress

Core implementation complete. See [TODO](docs/todo.md) for testing plan and future work.

---

## Benchmarks

Evaluate webtask on standard web agent benchmarks:

**[webtask-benchmarks](https://github.com/steve-z-wang/webtask-benchmarks)** - Evaluation framework for Mind2Web and other benchmarks

---

## Install

```bash
pip install pywebtask
playwright install chromium
```

---

## License

MIT
