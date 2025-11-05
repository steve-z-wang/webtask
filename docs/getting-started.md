
# Getting Started

This guide will help you install webtask and run your first web automation task.


## Your First Task

Here's a complete example:

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

async def main():
    # Create Webtask manager (browser launches lazily)
    wt = Webtask(headless=False)  # Set headless=True for no GUI

    # Create LLM (choose Gemini or OpenAI)
    llm = GeminiLLM.create(model="gemini-2.5-flash")

    # Create agent with screenshot support (enabled by default)
    agent = await wt.create_agent(llm=llm, action_delay=1.0)

    # Execute a task
    result = await agent.execute("Go to google.com and search for 'cats'")

    print(f"Task completed: {result.completed}")
    print(f"Steps taken: {len(result.steps)}")

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

### Action Delay

```python
# Add delay between actions (seconds)
agent = await wt.create_agent(llm=llm, action_delay=1.5)
```

### Screenshot Mode

```python
# With screenshots (default, more accurate)
agent = await wt.create_agent(llm=llm, use_screenshot=True)

# Without screenshots (faster, cheaper)
agent = await wt.create_agent(llm=llm, use_screenshot=False)
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
