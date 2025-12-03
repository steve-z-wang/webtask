
# Agent

Main interface for web automation.

## Constructor

```python
Agent(
    llm: LLM,
    context: Context,
    mode: str = "text",
    wait_after_action: float = 1.0
)
```

**Parameters:**
- `llm` - LLM instance for reasoning
- `context` - Browser context
- `mode` - Agent mode: "text" (DOM-based), "visual" (screenshots), "full" (both)
- `wait_after_action` - Default wait time after each action in seconds (default: 1.0)

## Methods

### `do()`

```python
async def do(
    task: str,
    max_steps: int = 20,
    wait_after_action: Optional[float] = None,
    files: Optional[List[str]] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    dom_mode: str = "accessibility"
) -> Result
```

Execute a task with natural language.

**Parameters:**
- `task` - Task description
- `max_steps` - Maximum steps to execute (default: 20)
- `wait_after_action` - Wait time after each action (uses agent default if not specified)
- `files` - Optional list of file paths for upload
- `output_schema` - Optional Pydantic model for structured output
- `dom_mode` - DOM mode: "accessibility" or "dom" (default: "accessibility")

**Returns:** Result with optional output and feedback

**Raises:** `TaskAbortedError` if task is aborted

**Example:**
```python
result = await agent.do("Add 2 screws to the cart")
print(result.feedback)

# With structured output
from pydantic import BaseModel

class ProductInfo(BaseModel):
    name: str
    price: float

result = await agent.do("Extract product info", output_schema=ProductInfo)
print(f"{result.output.name}: ${result.output.price}")
```

### `verify()`

```python
async def verify(
    condition: str,
    max_steps: int = 10,
    wait_after_action: Optional[float] = None,
    dom_mode: str = "accessibility"
) -> Verdict
```

Check if a condition is true.

**Parameters:**
- `condition` - Condition to check
- `max_steps` - Maximum steps (default: 10)
- `wait_after_action` - Wait time after each action (uses agent default if not specified)
- `dom_mode` - DOM mode (default: "accessibility")

**Returns:** Verdict that can be used as boolean

**Raises:** `TaskAbortedError` if verification is aborted

**Example:**
```python
verdict = await agent.verify("the cart contains 7 items")

if verdict:
    print("Success!")

assert verdict == True
```

### `extract()`

```python
async def extract(
    what: str,
    output_schema: Optional[Type[BaseModel]] = None,
    max_steps: int = 10,
    wait_after_action: Optional[float] = None,
    dom_mode: str = "accessibility"
) -> str | BaseModel
```

Extract information from the current page.

**Parameters:**
- `what` - What to extract in natural language
- `output_schema` - Optional Pydantic model for structured output
- `max_steps` - Maximum steps (default: 10)
- `wait_after_action` - Wait time after each action (uses agent default if not specified)
- `dom_mode` - DOM mode (default: "accessibility")

**Returns:** str if no output_schema provided, otherwise instance of output_schema

**Raises:** `TaskAbortedError` if extraction is aborted

**Example:**
```python
# Simple string extraction
price = await agent.extract("total price")
print(f"Price: {price}")

# Structured extraction
from pydantic import BaseModel

class ProductInfo(BaseModel):
    name: str
    price: float
    in_stock: bool

product = await agent.extract("product information", ProductInfo)
print(f"{product.name}: ${product.price}")
```

### `goto()`

```python
async def goto(url: str) -> None
```

Navigate to a URL.

**Example:**
```python
await agent.goto("example.com")
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
- `path` - Optional file path to save screenshot
- `full_page` - Screenshot the full scrollable page (default: False)

**Returns:** Screenshot as bytes (PNG format)

**Example:**
```python
# Save to file
await agent.screenshot("page.png")

# Full page screenshot
await agent.screenshot("full.png", full_page=True)

# Get bytes without saving
screenshot_bytes = await agent.screenshot()
```

### `wait()`

```python
async def wait(seconds: float) -> None
```

Wait for a specific amount of time.

**Parameters:**
- `seconds` - Number of seconds to wait

**Example:**
```python
await agent.wait(2.0)  # Wait 2 seconds
```

### `wait_for_load()`

```python
async def wait_for_load(timeout: int = 10000) -> None
```

Wait for the current page to fully load.

**Parameters:**
- `timeout` - Maximum time to wait in milliseconds (default: 10000ms = 10s)

**Raises:**
- `RuntimeError` if no page is active
- `TimeoutError` if page doesn't load within timeout

**Example:**
```python
await agent.goto("example.com")
await agent.wait_for_load()
```

### `wait_for_network_idle()`

```python
async def wait_for_network_idle(timeout: int = 10000) -> None
```

Wait for network to be idle (no requests for 500ms). Useful for SPAs and pages with AJAX requests.

**Parameters:**
- `timeout` - Maximum time to wait in milliseconds (default: 10000ms = 10s)

**Raises:**
- `RuntimeError` if no page is active
- `TimeoutError` if network doesn't become idle within timeout

**Example:**
```python
await agent.do("Click the search button")
await agent.wait_for_network_idle()  # Wait for results to load
```

### `clear_history()`

```python
def clear_history() -> None
```

Clear conversation history. Resets the agent's memory of previous tasks, starting fresh.

**Example:**
```python
await agent.do("Add item to cart")
await agent.do("Checkout")  # Agent remembers cart context

agent.clear_history()  # Start fresh

await agent.do("Search for shoes")  # No memory of previous tasks
```

### `get_debug_context()`

```python
async def get_debug_context() -> str
```

Get the text context that the LLM sees (for debugging). Returns the DOM snapshot and tabs context as a string. Useful for debugging when elements can't be found in text mode.

**Returns:** The text representation of the current page state

**Example:**
```python
context = await agent.get_debug_context()
print(context)  # See what the LLM sees
```

### `get_current_page()`

```python
def get_current_page() -> Optional[Page]
```

Get the current active page.

**Returns:** Current Page instance, or None if no page is active

**Example:**
```python
page = agent.get_current_page()
if page:
    print(f"Current URL: {page.url}")
```

### `focus_tab()`

```python
def focus_tab(page: Page) -> None
```

Focus a specific tab.

**Parameters:**
- `page` - Page instance to focus

**Example:**
```python
pages = agent.browser.get_pages()
agent.focus_tab(pages[0])  # Focus first tab
```
