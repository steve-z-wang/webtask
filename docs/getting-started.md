
# Getting Started

This guide will help you install webtask and run your first web automation task.


## Your First Task

Here's a complete example:

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import Gemini

async def main():
    # Create Webtask manager (browser launches lazily)
    wt = Webtask(headless=False)  # Set headless=True for no GUI

    # Create LLM (choose Gemini or OpenAI)
    llm = Gemini(model="gemini-2.5-flash")

    # Create agent with screenshot support (enabled by default)
    agent = await wt.create_agent(llm=llm)

    # Execute a task
    result = await agent.do("Go to google.com and search for 'cats'")

    print(f"Task status: {result.status}")
    print(f"Feedback: {result.feedback}")

    # Clean up
    await wt.close()

# Run it
asyncio.run(main())
```


## Configuration Options

### Headless Mode

```python
# Show browser (good for debugging)
wt = Webtask(headless=False)

# Hide browser (good for production)
wt = Webtask(headless=True)
```

### Stateful Mode

```python
# Stateful mode - maintains conversation history across tasks
llm = Gemini(model="gemini-2.5-flash")
agent = await wt.create_agent(llm=llm, stateful=True)

# Execute multiple related tasks
await agent.do("Go to google.com")
await agent.do("Search for cats")  # Agent remembers it's on Google
```


## Troubleshooting

### Browser not launching

Make sure you installed Playwright browsers:
```bash
playwright install chromium
```

### API key errors

Check that your environment variable is set:
```bash
echo $GEMINI_API_KEY  # or $OPENAI_API_KEY
```

### Import errors

Make sure you installed the package:
```bash
pip install pywebtask
```
