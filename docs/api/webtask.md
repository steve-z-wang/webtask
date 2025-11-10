
# Webtask

Main manager class for browser lifecycle.

Manages browser lifecycle and creates agents with various configurations. Browser is launched lazily on first agent creation.

## Constructor

```python
Webtask(headless: bool = False, browser_type: str = "chromium")
```

**Parameters:**
- `headless` (bool): Run browser in headless mode. Default: `False`
- `browser_type` (str): Browser type to use. Default: `"chromium"`

**Example:**
```python
from webtask import Webtask

# Show browser (good for debugging)
wt = Webtask(headless=False)

# Hide browser (good for production)
wt = Webtask(headless=True)
```

## Methods

### `create_agent()`

```python
async def create_agent(
    llm: LLM,
    cookies=None,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with new browser session. Launches browser on first call.

**Parameters:**
- `llm` (LLM): LLM instance for reasoning (OpenAILLM or GeminiLLM)
- `cookies`: Optional cookies for the session
- `use_screenshot` (bool): Use screenshots with bounding boxes. Default: `True`
- `selector_llm` (Optional[LLM]): Optional separate LLM for element selection. Defaults to main `llm`

**Returns:** Agent instance with new session

**Example:**
```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

wt = Webtask(headless=False)
llm = GeminiLLM.create(model="gemini-2.5-flash")
agent = await wt.create_agent(llm=llm)

# Without screenshots (faster, cheaper)
agent = await wt.create_agent(llm=llm, use_screenshot=False)
```

### `create_agent_with_browser()`

```python
async def create_agent_with_browser(
    llm: LLM,
    browser: Browser,
    cookies=None,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with existing browser.

**Parameters:**
- `llm` (LLM): LLM instance for reasoning
- `browser` (Browser): Existing Browser instance
- `cookies`: Optional cookies for the session
- `use_screenshot` (bool): Use screenshots with bounding boxes. Default: `True`
- `selector_llm` (Optional[LLM]): Optional separate LLM for element selection

**Returns:** Agent instance with new session from provided browser

**Example:**
```python
from webtask.integrations.browser.playwright import PlaywrightBrowser

# Create your own browser instance
browser = await PlaywrightBrowser.create_browser(headless=False)

# Create agent with it
agent = await wt.create_agent_with_browser(llm=llm, browser=browser)
```

### `create_agent_with_session()`

```python
def create_agent_with_session(
    llm: LLM,
    session: Session,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with existing session.

**Parameters:**
- `llm` (LLM): LLM instance for reasoning
- `session` (Session): Existing Session instance
- `use_screenshot` (bool): Use screenshots with bounding boxes. Default: `True`
- `selector_llm` (Optional[LLM]): Optional separate LLM for element selection

**Returns:** Agent instance with provided session

**Note:** This method is synchronous (not async)

**Example:**
```python
# Get session from browser
session = await browser.create_session()

# Create agent with that session
agent = wt.create_agent_with_session(llm=llm, session=session)
```

### `create_agent_with_page()`

```python
def create_agent_with_page(
    llm: LLM,
    page: Page,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with existing page (session-less mode).

**Parameters:**
- `llm` (LLM): LLM instance for reasoning
- `page` (Page): Existing Page instance
- `use_screenshot` (bool): Use screenshots with bounding boxes. Default: `True`
- `selector_llm` (Optional[LLM]): Optional separate LLM for element selection

**Returns:** Agent instance with provided page

**Note:** This method is synchronous (not async)

**Use case:** Connect to existing browser/page without managing the browser lifecycle

**Example:**
```python
# Get page from somewhere
page = await browser.create_page()

# Create agent with that page
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

## Complete Example

```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

async def main():
    # Create Webtask manager
    wt = Webtask(headless=False)

    # Create LLM
    llm = GeminiLLM.create(model="gemini-2.5-flash")

    # Create agent (browser launches here)
    agent = await wt.create_agent(llm=llm)

    # Use agent
    result = await agent.execute("search for cats")

    # Cleanup
    await wt.close()
```
