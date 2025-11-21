# Browser

Abstract base class for browser lifecycle management.

## Class Methods

### `create()`

```python
@classmethod
async def create(cls, **kwargs) -> Browser
```

Create and launch a new browser instance.

**Example:**
```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

browser = await PlaywrightBrowser.create(headless=True)
```

### `connect()`

```python
@classmethod
async def connect(cls, **kwargs) -> Browser
```

Connect to an existing browser instance.

**Example:**
```python
browser = await PlaywrightBrowser.connect("http://localhost:9222")
```

## Properties

### `contexts`

```python
contexts: List[Context]
```

Get all existing browser contexts.

**Example:**
```python
browser = await PlaywrightBrowser.connect("http://localhost:9222")
existing_contexts = browser.contexts
```

## Methods

### `get_default_context()`

```python
def get_default_context() -> Optional[Context]
```

Get the default (first) existing context, or None if no contexts exist.

**Example:**
```python
browser = await PlaywrightBrowser.connect("http://localhost:9222")
context = browser.get_default_context()
```

### `create_context()`

```python
async def create_context(**kwargs) -> Context
```

Create a new browser context.

**Example:**
```python
browser = await PlaywrightBrowser.create()
context = await browser.create_context()
```

### `close()`

```python
async def close() -> None
```

Close the browser instance.

**Example:**
```python
await browser.close()
```
