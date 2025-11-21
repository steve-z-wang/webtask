
# API Reference

## [Webtask](webtask.md)

Manages browser lifecycle and creates agents.

```python
wt = Webtask()
agent = await wt.create_agent(llm=llm)
```

## [Agent](agent.md)

Main interface for web automation.

```python
await agent.goto("https://example.com")
await agent.do("Click the login button")
verdict = await agent.verify("user is logged in")
```

## Browser

Low-level browser components for advanced use cases.

- **[Browser](browser.md)** - Browser lifecycle management
- **[Context](context.md)** - Isolated browsing sessions
- **[Page](page.md)** - Page operations
- **[Element](element.md)** - Element interactions

## [LLM](llm.md)

LLM providers and custom model integration.

```python
from webtask.integrations.llm import Gemini

llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
```

## [Result](data-classes.md)

Data classes returned by agent methods.

- `Result` - Returned by `agent.do()`
- `Verdict` - Returned by `agent.verify()`
- `Status` - Task status enum
