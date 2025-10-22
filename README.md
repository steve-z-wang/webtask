# webtask

Tell it what to do. Watch it work.

A web agent that runs browser tasks from plain English descriptions.

---

## What it does

Two ways to use it:

**High-level** - Give it a task, let it figure out the steps
**Low-level** - Tell it exactly what to do with natural language selectors

Uses LLMs to understand pages, plan actions, and select elements. Built with Playwright for the browser stuff.

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

# Create agent
agent = await wt.create_agent(llm=llm)
```

**High-level autonomous:**
```python
# Agent figures out the steps
await agent.execute("search for cats and click the first result")
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
```

No CSS selectors. No XPath. Just describe what you want.

---

## How it works

**High-level mode** - The agent loop:
1. Proposer looks at the page and task, decides next action
2. Executer runs it (click, type, navigate, etc.)
3. Verifier checks if done (coming soon)
4. Repeat until task complete

**Low-level mode** - You call methods directly:
- `agent.navigate(url)` - Go to a page
- `agent.select(description)` - Find element by natural language
- `element.click()`, `element.fill(text)` - Interact with elements
- `agent.wait(seconds)` - Wait for specific duration
- `agent.wait_for_idle()` - Wait for network/DOM to stabilize

Both modes use the same core: LLM sees cleaned DOM with element IDs like `button-0` instead of raw HTML. Clean input, clean output.

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
pip install webtask[playwright]
playwright install chromium
```

(Not actually published yet, clone the repo)

---

## License

MIT
