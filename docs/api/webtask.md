
# Webtask

Manages browser lifecycle and creates agents. Browser launches lazily on first agent creation.

## Constructor

```python
Webtask()
```

No parameters. Browser launches automatically when you create the first agent.

## Methods

### `create_agent()`

```python
async def create_agent(
    llm: LLM,
    mode: str = "text",
    stateful: bool = True,
    headless: bool = False,
    browser_type: str = "chromium"
) -> Agent
```

Create agent with new browser context.

**Parameters:**
- `llm` - LLM instance (Gemini, GeminiComputerUse, or Bedrock)
- `mode` - Agent mode: "text" (DOM-based), "visual" (screenshots), "full" (both)
- `stateful` - Maintain conversation history between do() calls (default: True)
- `headless` - Run browser without GUI (default: False)
- `browser_type` - "chromium", "firefox", or "webkit" (default: "chromium")

**Example:**
```python
from webtask import Webtask
from webtask.integrations.llm import GeminiComputerUse

wt = Webtask()

agent = await wt.create_agent(llm=GeminiComputerUse(), mode="visual")
agent = await wt.create_agent(llm=llm, mode="text", headless=True)
agent = await wt.create_agent(llm=llm, stateful=False)
```

### `create_agent_with_browser()`

```python
async def create_agent_with_browser(
    llm: LLM,
    browser: Browser,
    mode: str = "text",
    stateful: bool = True,
    use_existing_context: bool = True
) -> Agent
```

Create agent with existing browser.

**Example:**
```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

browser = await PlaywrightBrowser.connect("http://localhost:9222")
agent = await wt.create_agent_with_browser(llm=llm, browser=browser, mode="visual")
```

### `create_agent_with_context()`

```python
def create_agent_with_context(
    llm: LLM,
    context: Context,
    mode: str = "text",
    stateful: bool = True
) -> Agent
```

Create agent with existing context.

**Example:**
```python
context = browser.get_default_context()
agent = wt.create_agent_with_context(llm=llm, context=context, mode="text")
```

### `create_agent_with_page()`

```python
def create_agent_with_page(
    llm: LLM,
    page: Page,
    mode: str = "text",
    stateful: bool = True
) -> Agent
```

Create agent with existing page.

**Example:**
```python
page = await context.create_page()
agent = wt.create_agent_with_page(llm=llm, page=page, mode="visual")
```

### `close()`

```python
async def close() -> None
```

Close and cleanup all resources.

**Example:**
```python
await wt.close()
```
