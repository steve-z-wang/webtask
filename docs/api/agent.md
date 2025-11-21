
# Agent

Main interface for web automation.

## Methods

### `do()`

```python
async def do(
    task: str,
    max_steps: int = 10,
    wait_after_action: float = 0.2,
    mode: str = "accessibility",
    output_schema: Optional[Type[BaseModel]] = None
) -> Result
```

Execute a task with natural language.

**Parameters:**
- `task` - Task description
- `max_steps` - Maximum steps to execute (default: 10)
- `wait_after_action` - Wait time after each action in seconds (default: 0.2)
- `mode` - DOM mode: "accessibility" or "all" (default: "accessibility")
- `output_schema` - Optional Pydantic model for structured output

**Returns:** Result with status and feedback

**Example:**
```python
await agent.do("Add 2 screws to the cart")

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
    wait_after_action: float = 0.2,
    mode: str = "accessibility"
) -> Verdict
```

Check if a condition is true.

**Parameters:**
- `condition` - Condition to check
- `max_steps` - Maximum steps (default: 10)
- `wait_after_action` - Wait time after each action (default: 0.2)
- `mode` - DOM mode (default: "accessibility")

**Returns:** Verdict that can be used as boolean

**Example:**
```python
verdict = await agent.verify("the cart contains 7 items")

if verdict:
    print("Success!")

assert verdict == True
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
