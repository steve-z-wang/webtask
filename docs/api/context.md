# Context

Abstract base class for browser context management.

A context is an isolated browsing session with its own cookies and storage. Equivalent to Playwright's BrowserContext.

## Properties

### `pages`

```python
pages: List[Page]
```

Get all existing pages in this context.

**Example:**
```python
context = await browser.create_context()
existing_pages = context.pages
print(f"Number of pages: {len(existing_pages)}")
```

## Methods

### `create_page()`

```python
async def create_page() -> Page
```

Create a new page/tab in this context.

**Example:**
```python
context = await browser.create_context()
page = await context.create_page()
await page.navigate("https://example.com")
```

### `close()`

```python
async def close() -> None
```

Close the context and all its pages.

**Example:**
```python
await context.close()
```

## Complete Example

```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

# Create browser and context
browser = await PlaywrightBrowser.create(headless=False)
context = await browser.create_context()

# Create pages
page1 = await context.create_page()
page2 = await context.create_page()

await page1.navigate("https://example.com")
await page2.navigate("https://google.com")

# Check all pages
print(f"Total pages: {len(context.pages)}")

# Cleanup
await context.close()
await browser.close()
```
