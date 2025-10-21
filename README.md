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

**High-level autonomous:**
```python
from webtask import Agent

agent = Agent()

# Agent figures out the steps
agent.execute("search for cats and click the first result")
```

**Low-level imperative:**
```python
from webtask import Agent

agent = Agent()

# You control the steps, agent handles the selectors
agent.navigate("https://google.com")
agent.select("search box").type("cats")
agent.select("search button").click()
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
- `.click()`, `.type()`, `.fill()` - Do stuff with it

Both modes use the same core: LLM sees cleaned DOM with element IDs like `button-0` instead of raw HTML. Clean input, clean output.

---

## Architecture

```
Agent                # Main interface (execute + select/navigate/etc)
├── Proposer         # Plans next action (high-level mode)
├── Executer         # Runs actions
├── LLMBrowser       # Maps element IDs ↔ selectors
└── Tools            # navigate, click, fill, etc.

Browser Layer        # Playwright wrapper
DOM Processing       # Filters, serializers
LLM Integration      # Context builder, token counting
```

Clean separation: DOM layer doesn't know about LLMs. Browser doesn't know about element IDs. Agent exposes both autonomous and imperative interfaces.

---

## Status

🚧 Work in progress

What's done:
- Basic agent architecture
- Tool system (navigate, click, fill)
- DOM filtering and element mapping
- Proposer and Executer roles

What's next:
- Verifier role
- Error recovery
- More tools
- Real testing on Mind2Web

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
