# webtask

LLM-powered web automation library with autonomous agents and natural language selectors.

---

## What it does

Three ways to use it:

**High-level** - Give it a task, let it figure out the steps
**Step-by-step** - Execute tasks one step at a time for debugging/control
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
result = await agent.execute("search for cats and click the first result")
print(f"Completed: {result.completed}")
```

**Step-by-step execution:**
```python
# Execute task one step at a time
agent.set_task("add 2 items to cart")

for i in range(10):
    step = await agent.run_step()

    print(f"Step {i+1}: {len(step.proposals)} actions")
    print(f"Verification: {step.verification.message}")

    if step.verification.complete:
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
1. Proposer looks at the page and task, decides next action
2. Executer runs it (click, type, navigate, etc.)
3. Verifier checks if task complete
4. Repeat until done

**Step-by-step mode** - Same as high-level but you control the loop:
- `agent.set_task(description)` - Set the task
- `agent.execute_step()` - Execute one step (propose → execute → verify)
- `agent.clear_history()` - Reset for new task

**Low-level mode** - You call methods directly:
- `agent.navigate(url)` - Go to a page
- `agent.select(description)` - Find element by natural language
- `element.click()`, `element.fill(text)`, `element.type(text)` - Interact with elements
- `agent.wait(seconds)` - Wait for specific duration
- `agent.wait_for_idle()` - Wait for network/DOM to stabilize
- `agent.screenshot(path)` - Capture page screenshot

All modes use the same core: LLM sees cleaned DOM with element IDs like `button-0` instead of raw HTML. Clean input, clean output.

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
