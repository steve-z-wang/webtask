
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
    stateful: bool = True,
    headless: bool = False,
    browser_type: str = "chromium"
) -> Agent
```

Create agent with new browser context.

**Parameters:**
- `llm` - LLM instance (Gemini or Bedrock)
- `stateful` - Maintain conversation history between do() calls (default: True)
- `headless` - Run browser without GUI (default: False)
- `browser_type` - "chromium", "firefox", or "webkit" (default: "chromium")

**Example:**
```python
from webtask import Webtask
from webtask.integrations.llm import Gemini
import os

wt = Webtask()

llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

# Visible browser (default)
agent = await wt.create_agent(llm=llm)

# Headless browser
agent = await wt.create_agent(llm=llm, headless=True)

# Non-stateful agent
agent = await wt.create_agent(llm=llm, stateful=False)
```

### `create_agent_with_browser()`

```python
async def create_agent_with_browser(
    llm: LLM,
    browser: Browser,
    stateful: bool = True,
    use_existing_context: bool = True
) -> Agent
```

Create agent with existing browser. Uses existing context by default.

**Example:**
```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

# Connect to existing browser
browser = await PlaywrightBrowser.connect("http://localhost:9222")
agent = await wt.create_agent_with_browser(llm=llm, browser=browser)

# Force new isolated window
agent = await wt.create_agent_with_browser(
    llm=llm,
    browser=browser,
    use_existing_context=False
)
```

### `create_agent_with_context()`

```python
def create_agent_with_context(
    llm: LLM,
    context: Context,
    stateful: bool = True
) -> Agent
```

Create agent with existing context.

**Example:**
```python
context = browser.get_default_context()
agent = wt.create_agent_with_context(llm=llm, context=context)
```

### `create_agent_with_page()`

```python
def create_agent_with_page(
    llm: LLM,
    page: Page,
    stateful: bool = True
) -> Agent
```

Create agent with existing page.

**Example:**
```python
page = await context.create_page()
agent = wt.create_agent_with_page(llm=llm, page=page)
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
