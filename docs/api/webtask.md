
# Webtask

Main manager class for browser lifecycle.

Manages browser lifecycle and creates agents with various configurations. Browser is launched lazily on first agent creation.


## Methods

### `create_agent()`

```python
async def create_agent(
    llm: LLM,
    cookies=None,
    action_delay: float = 1.0,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with new browser session. Launches browser on first call.

**Parameters:**
- `llm` (LLM): LLM instance for reasoning (OpenAILLM or GeminiLLM)
- `cookies`: Optional cookies for the session
- `action_delay` (float): Delay in seconds after actions. Default: `1.0`
- `use_screenshot` (bool): Use screenshots with bounding boxes. Default: `True`
- `selector_llm` (Optional[LLM]): Optional separate LLM for element selection. Defaults to main `llm`

**Returns:** Agent instance with new session

**Example:**
```python
from webtask.integrations.llm import GeminiLLM

llm = GeminiLLM.create(model="gemini-2.5-flash")
agent = await wt.create_agent(llm=llm, action_delay=1.5)
```


### `create_agent_with_session()`

```python
def create_agent_with_session(
    llm: LLM,
    session: Session,
    action_delay: float = 1.0,
    use_screenshot: bool = True,
    selector_llm: Optional[LLM] = None
) -> Agent
```

Create agent with existing session.

**Parameters:**
- `llm` (LLM): LLM instance for reasoning
- `session` (Session): Existing Session instance
- `action_delay` (float): Delay in seconds after actions. Default: `1.0`
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


### `close()`

```python
async def close() -> None
```

Close and cleanup all resources.

**Example:**
```python
await wt.close()
```

