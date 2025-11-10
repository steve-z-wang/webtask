
# Agent

Main interface for web automation tasks.

Provides two modes of interaction:
- **Autonomous mode**: `execute(task)` - Agent figures out the steps
- **Direct control mode**: `navigate()`, `select()`, etc. - You control the flow with natural language

## Autonomous Mode

### `execute()`

```python
async def execute(
    task_description: str,
    max_cycles: int = 10,
    resources: Optional[Dict[str, str]] = None
) -> TaskExecution
```

Execute a task autonomously using manager-worker architecture.

**Parameters:**
- `task_description` (str): Task description in natural language
- `max_cycles` (int): Maximum manager-worker cycles. Default: `10`
- `resources` (Optional[Dict[str, str]]): Optional dict of file resources (name → path)

**Returns:** TaskExecution with status, history, and subtask queue

**Example:**
```python
from webtask import TaskStatus

result = await agent.execute("search google for cats", max_cycles=15)
print(f"Status: {result.status}")
print(f"Sessions: {len(result.history)}")

if result.status == TaskStatus.COMPLETED:
    print("Task completed successfully!")
elif result.status == TaskStatus.ABORTED:
    print(f"Task aborted: {result.failure_reason}")
```

## Direct Control Mode

### `navigate()`

```python
async def navigate(url: str) -> None
```

Navigate to a URL.

**Parameters:**
- `url` (str): URL to navigate to

**Example:**
```python
await agent.navigate("https://example.com")
```

### `select()`

```python
async def select(description: str) -> Element
```

Select element by natural language description.

**Parameters:**
- `description` (str): Natural language description of the element

**Returns:** Element with click(), fill(), type() methods

**Raises:**
- RuntimeError: If no page is opened
- ValueError: If LLM fails to find a matching element

**Example:**
```python
search_box = await agent.select("search box")
await search_box.fill("cats")

button = await agent.select("search button")
await button.click()
```

### `wait()`

```python
async def wait(seconds: float) -> None
```

Wait for a specific amount of time.

**Parameters:**
- `seconds` (float): Number of seconds to wait

**Example:**
```python
await agent.wait(2.0)  # Wait 2 seconds
```

### `wait_for_idle()`

```python
async def wait_for_idle(timeout: int = 30000) -> None
```

Wait for page to be idle (network and DOM stable).

**Parameters:**
- `timeout` (int): Maximum time to wait in milliseconds. Default: `30000`

**Raises:**
- RuntimeError: If no page is opened
- TimeoutError: If page doesn't become idle within timeout

**Example:**
```python
await agent.navigate("https://example.com")
await agent.wait_for_idle()  # Wait for page to fully load
```

### `screenshot()`

```python
async def screenshot(
    path: Optional[str] = None,
    full_page: bool = False
) -> bytes
```

Take a screenshot of the current page.

**Parameters:**
- `path` (Optional[str]): Optional file path to save screenshot
- `full_page` (bool): Whether to screenshot the full scrollable page. Default: `False`

**Returns:** Screenshot as bytes (PNG format)

**Raises:**
- RuntimeError: If no page is opened

**Example:**
```python
# Save to file
await agent.screenshot("page.png")

# Full page screenshot
await agent.screenshot("full.png", full_page=True)

# Get bytes
screenshot_bytes = await agent.screenshot()
```

## Multi-Page Management

### `open_page()`

```python
async def open_page(url: Optional[str] = None) -> Page
```

Open a new page and switch to it.

**Parameters:**
- `url` (Optional[str]): Optional URL to navigate to

**Returns:** The new Page instance

**Raises:**
- RuntimeError: If no session is available

**Example:**
```python
page2 = await agent.open_page("https://example.com")
```

### `close_page()`

```python
async def close_page(page: Optional[Page] = None) -> None
```

Close a page (closes current page if page=None).

**Parameters:**
- `page` (Optional[Page]): Page to close (defaults to current page)

**Example:**
```python
await agent.close_page()  # Close current page
await agent.close_page(page2)  # Close specific page
```

### `get_pages()`

```python
def get_pages() -> List[Page]
```

Get all open pages.

**Returns:** List of Page instances

**Example:**
```python
pages = agent.get_pages()
print(f"Total pages: {len(pages)}")
```

### `get_current_page()`

```python
def get_current_page() -> Optional[Page]
```

Get the current active page.

**Returns:** Current Page or None

**Example:**
```python
current = agent.get_current_page()
if current:
    print(f"Current URL: {current.url}")
```

### `set_page()`

```python
def set_page(page: Page) -> None
```

Set/switch to a specific page.

**Parameters:**
- `page` (Page): Page instance to set as current

**Example:**
```python
page1 = agent.get_pages()[0]
agent.set_page(page1)  # Switch to page 1
```

## Properties

### `page_count`

```python
page_count: int
```

Number of open pages.

**Example:**
```python
print(f"Open pages: {agent.page_count}")
```

## Advanced

### `set_session()`

```python
def set_session(session: Session) -> None
```

Set/inject a browser session.

**Parameters:**
- `session` (Session): Session instance to use

**Example:**
```python
agent.set_session(my_session)
```

### `close()`

```python
async def close() -> None
```

Close and cleanup all resources.

**Example:**
```python
await agent.close()
```

## Complete Example

```python
from webtask import Webtask, TaskStatus
from webtask.integrations.llm import GeminiLLM

async def main():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    # Autonomous mode
    result = await agent.execute("search for cats and click first result")
    if result.status == TaskStatus.COMPLETED:
        print("Task completed!")

    # Direct control mode
    await agent.navigate("https://example.com")
    search = await agent.select("search box")
    await search.fill("dogs")
    await (await agent.select("search button")).click()
    await agent.wait_for_idle()
    await agent.screenshot("result.png")

    await wt.close()
```
