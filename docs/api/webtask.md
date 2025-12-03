
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
    mode: str = "dom",
    wait_after_action: float = 1.0,
    headless: bool = False,
    browser_type: str = "chromium"
) -> Agent
```

Create agent with new browser context.

**Parameters:**
- `llm` - LLM instance (Gemini, GeminiComputerUse, or Bedrock)
- `mode` - Agent mode: "dom" (element IDs) or "pixel" (screen coordinates)
- `wait_after_action` - Wait time in seconds after each action (default: 1.0)
- `headless` - Run browser without GUI (default: False)
- `browser_type` - "chromium", "firefox", or "webkit" (default: "chromium")

**Example:**
```python
from webtask import Webtask
from webtask.integrations.llm import GeminiComputerUse

wt = Webtask()

agent = await wt.create_agent(llm=GeminiComputerUse(), mode="pixel")
agent = await wt.create_agent(llm=llm, mode="dom", headless=True)
agent = await wt.create_agent(llm=llm, wait_after_action=2.0)  # Slower network
```

### `create_agent_with_browser()`

```python
async def create_agent_with_browser(
    llm: LLM,
    browser: Browser,
    mode: str = "dom",
    wait_after_action: float = 1.0,
    use_existing_context: bool = True
) -> Agent
```

Create agent with existing browser.

**Example:**
```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

browser = await PlaywrightBrowser.connect("http://localhost:9222")
agent = await wt.create_agent_with_browser(llm=llm, browser=browser, mode="pixel")
```

### `create_agent_with_context()`

```python
def create_agent_with_context(
    llm: LLM,
    context: Context,
    mode: str = "dom",
    wait_after_action: float = 1.0
) -> Agent
```

Create agent with existing context.

**Example:**
```python
context = browser.get_default_context()
agent = wt.create_agent_with_context(llm=llm, context=context, mode="dom")
```

### `create_agent_with_page()`

```python
def create_agent_with_page(
    llm: LLM,
    page: Page,
    mode: str = "text",
    wait_after_action: float = 1.0
) -> Agent
```

Create agent with existing page.

**Example:**
```python
page = await context.create_page()
agent = wt.create_agent_with_page(llm=llm, page=page, mode="pixel")
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
