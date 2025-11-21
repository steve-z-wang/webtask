
# Page

Abstract base class for browser page management.

## Properties

### `url`

```python
url: str
```

Get current page URL.

## Methods

### `navigate()`

```python
async def navigate(url: str) -> None
```

Navigate to a URL.

### `select()`

```python
async def select(selector: str) -> List[Element]
```

Select all elements matching the selector.

**Parameters:**
- `selector` - CSS selector or XPath string

**Returns:** List of Elements (may be empty)

### `select_one()`

```python
async def select_one(selector: str) -> Element
```

Select a single element matching the selector.

**Parameters:**
- `selector` - CSS selector or XPath string

**Raises:** ValueError if no elements match or multiple elements match

### `wait_for_load()`

```python
async def wait_for_load(timeout: int = 10000) -> None
```

Wait for page to fully load.

**Parameters:**
- `timeout` - Maximum time to wait in milliseconds (default: 10000)

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

### `keyboard_type()`

```python
async def keyboard_type(
    text: str,
    clear: bool = False,
    delay: float = 80
) -> None
```

Type text using keyboard into the currently focused element.

**Parameters:**
- `text` - Text to type
- `clear` - Clear existing text before typing (default: False)
- `delay` - Delay between keystrokes in milliseconds (default: 80)

### `evaluate()`

```python
async def evaluate(script: str) -> Any
```

Execute JavaScript in the page context.

**Parameters:**
- `script` - JavaScript code to execute

**Returns:** Result of the script execution (JSON-serializable values)

### `get_cdp_dom_snapshot()`

```python
async def get_cdp_dom_snapshot() -> Dict[str, Any]
```

Get a CDP DOM snapshot of the current page.

**Returns:** CDP DOM snapshot data

### `get_cdp_accessibility_tree()`

```python
async def get_cdp_accessibility_tree() -> Dict[str, Any]
```

Get a CDP accessibility tree of the current page.

**Returns:** CDP accessibility tree data

### `close()`

```python
async def close() -> None
```

Close the page.

