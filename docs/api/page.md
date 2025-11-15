
# Page

Abstract base class for browser page management.

Simple adapter over browser automation libraries (Playwright, Selenium, etc.). Typically accessed through Agent methods rather than directly.


## Methods

### `navigate()`

```python
async def navigate(url: str)
```

Navigate to a URL.

**Parameters:**
- `url` (str): URL to navigate to

**Example:**
```python
await page.navigate("https://google.com")
```


### `select_one()`

```python
async def select_one(selector: str) -> Element
```

Select a single element matching the selector.

**Parameters:**
- `selector` (str): CSS selector or XPath string

**Returns:** Single Element

**Raises:** ValueError if no elements match or multiple elements match

**Example:**
```python
# Get single element
submit_button = await page.select_one("button#submit")
```


### `wait_for_idle()`

```python
async def wait_for_idle(timeout: int = 30000)
```

Wait for page to be idle (network and DOM stable).

**Parameters:**
- `timeout` (int): Maximum time to wait in milliseconds. Default: `30000` (30 seconds)

**Raises:** TimeoutError if page doesn't become idle within timeout

**Example:**
```python
await page.wait_for_idle()  # Wait up to 30 seconds
await page.wait_for_idle(timeout=10000)  # Wait up to 10 seconds
```


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
- `text` (str): Text to type
- `clear` (bool): Clear existing text before typing. Default: `False`
- `delay` (float): Delay between keystrokes in milliseconds. Default: `80`

**Example:**
```python
element = await page.select_one("#input")
await element.click()  # Focus the element
await page.keyboard_type("Hello World", delay=100)
```


### `get_cdp_snapshot()`

```python
async def get_cdp_snapshot() -> Dict[str, Any]
```

Get a CDP (Chrome DevTools Protocol) snapshot of the current page.

**Returns:** CDP snapshot data (raw dictionary from DOMSnapshot.captureSnapshot)

**Note:** This is a low-level method typically used internally. Use `get_snapshot()` for a higher-level interface.

**Example:**
```python
cdp_data = await page.get_cdp_snapshot()
```


## Complete Example

```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

# Create browser and page
browser = await PlaywrightBrowser.create(headless=False)
session = await browser.create_session()
page = await session.create_page()

# Navigate
await page.navigate("https://google.com")

# Wait for page to load
await page.wait_for_idle()

# Select elements
search_input = await page.select_one("input[name='q']")
await search_input.fill("web automation")

# Take screenshot
await page.screenshot("google.png")

# Execute JavaScript
title = await page.evaluate("document.title")
print(f"Page title: {title}")

# Cleanup
await page.close()
await browser.close()
```

