
# Agent

Main interface for web automation.

## Methods

### `do()`

```python
async def do(
    task: str,
    max_steps: int = 20,
    wait_after_action: float = 0.2,
    resources: Optional[Dict[str, str]] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    mode: str = "accessibility"
) -> Result
```

Execute a task with natural language.

**Parameters:**
- `task` - Task description
- `max_steps` - Maximum steps to execute (default: 20)
- `wait_after_action` - Wait time after each action in seconds (default: 0.2)
- `resources` - Optional dict of file resources (name -> path)
- `output_schema` - Optional Pydantic model for structured output
- `mode` - DOM mode: "accessibility" or "dom" (default: "accessibility")

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
    wait_after_action: float = 0.2,
    mode: str = "accessibility"
) -> str | BaseModel
```

Extract information from the current page.

**Parameters:**
- `what` - What to extract in natural language
- `output_schema` - Optional Pydantic model for structured output
- `max_steps` - Maximum steps (default: 10)
- `wait_after_action` - Wait time after each action (default: 0.2)
- `mode` - DOM mode (default: "accessibility")

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
