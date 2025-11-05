
# Agent

Main interface for web automation tasks.

Provides three modes of interaction:
- **High-level autonomous**: `execute(task)` - Agent figures out the steps
- **Step-by-step**: `set_task()` + `run_step()` - Manual control over execution loop
- **Low-level imperative**: `navigate()`, `select()`, etc. - Direct control with natural language


## High-Level Methods

### `execute()`

```python
async def execute(
    task: str,
    max_steps: int = 10,
    resources: Optional[Dict[str, str]] = None,
    screenshot_on_failure: bool = False,
    failure_screenshot_path: Optional[str] = None
) -> TaskResult
```

Execute a task autonomously.

**Parameters:**
- `task` (str): Task description in natural language
- `max_steps` (int): Maximum number of steps before giving up. Default: `10`
- `resources` (Optional[Dict[str, str]]): Optional dict of file resources (name → path)
- `screenshot_on_failure` (bool): Capture screenshot when task fails. Default: `False`
- `failure_screenshot_path` (Optional[str]): Path to save failure screenshot (auto-generated if not specified)

**Returns:** TaskResult with completion status, steps, and final message

**Example:**
```python
result = await agent.execute("search google for cats", max_steps=15)
print(f"Completed: {result.completed}")
print(f"Steps: {len(result.steps)}")
```

**With failure screenshot:**
```python
result = await agent.execute(
    "find product XYZ",
    screenshot_on_failure=True,
    failure_screenshot_path="failed.png"
)
```


### `run_step()`

```python
async def run_step() -> Step
```

Execute one step of the current task.

**Returns:** Step with proposal and execution results

**Raises:** RuntimeError if no task is set (call `set_task()` first)

**Example:**
```python
agent.set_task("search for cats")

for i in range(10):
    step = await agent.run_step()
    print(f"Step {i+1}: {len(step.proposal.actions)} actions")

    if step.proposal.complete:
        break
```


### `select()`

```python
async def select(description: str) -> Element
```

Select element by natural language description.

**Parameters:**
- `description` (str): Natural language description of element

**Returns:** Browser Element with `.click()`, `.fill()`, `.type()` methods

**Raises:**
- RuntimeError: If no page is opened
- ValueError: If LLM fails to find a matching element

**Example:**
```python
search_box = await agent.select("search input field")
await search_box.fill("cats")

button = await agent.select("search button")
await button.click()
```


### `wait_for_idle()`

```python
async def wait_for_idle(timeout: int = 30000)
```

Wait for page to be idle (network and DOM stable).

**Parameters:**
- `timeout` (int): Maximum time to wait in milliseconds. Default: `30000` (30 seconds)

**Raises:**
- RuntimeError: If no page is opened
- TimeoutError: If page doesn't become idle within timeout

**Example:**
```python
await agent.wait_for_idle()  # Wait up to 30 seconds
await agent.wait_for_idle(timeout=10000)  # Wait up to 10 seconds
```


## Multi-Page Methods

### `open_page()`

```python
async def open_page(url: Optional[str] = None) -> Page
```

Open a new page and switch to it.

**Parameters:**
- `url` (Optional[str]): Optional URL to navigate to

**Returns:** The new Page instance

**Raises:** RuntimeError if no session is available

**Example:**
```python
# Open new blank page
new_page = await agent.open_page()

# Open new page and navigate
new_page = await agent.open_page("https://github.com")
```


### `get_current_page()`

```python
def get_current_page() -> Optional[Page]
```

Get the current active page.

**Returns:** Current Page instance or None

**Example:**
```python
current = agent.get_current_page()
print(f"Current URL: {current.url}")
```


### `page_count`

```python
@property
def page_count() -> int
```

Number of open pages.

**Example:**
```python
print(f"Pages open: {agent.page_count}")
```


### `set_session()`

```python
def set_session(session: Session) -> None
```

Set or update the session.

Enables multi-page operations after initialization.

**Parameters:**
- `session` (Session): Session instance for creating pages

**Example:**
```python
session = await browser.create_session()
agent.set_session(session)
```


## Complete Example

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

async def main():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    # High-level autonomous
    result = await agent.execute("search google for cats")

    # Step-by-step
    agent.set_task("add item to cart")
    for i in range(10):
        step = await agent.run_step()
        if step.proposal.complete:
            break

    # Low-level imperative
    await agent.navigate("https://google.com")
    search_box = await agent.select("search box")
    await search_box.fill("web automation")
    await agent.wait_for_idle()
    await agent.screenshot("result.png")

    await wt.close()

asyncio.run(main())
```
