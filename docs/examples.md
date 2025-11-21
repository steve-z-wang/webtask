# Examples

## Complete Workflow

This example demonstrates all three core methods: `do()`, `extract()`, and `verify()`.

```python
import asyncio
from webtask import Webtask, TaskAbortedError
from webtask.integrations.llm import Gemini
from pydantic import BaseModel
import os

class CartSummary(BaseModel):
    item_count: int
    total_price: float

async def main():
    wt = Webtask()

    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm)

    await agent.goto("practicesoftwaretesting.com")

    # do() - Execute tasks
    await agent.do("Add 2 Flat-Head Wood Screws to the cart")
    await agent.do("Add 5 Cross-head screws to the cart")
    await agent.do("Go to the cart page")

    # extract() - Get information from the page
    total = await agent.extract("total price")
    print(f"Total: {total}")

    # extract() with structured output
    summary = await agent.extract("cart summary", CartSummary)
    print(f"Items: {summary.item_count}, Total: ${summary.total_price}")

    # verify() - Check conditions
    verdict = await agent.verify("the cart contains 7 items")
    if verdict:
        print("Cart verified!")

    await wt.close()

asyncio.run(main())
```

## Error Handling

```python
from webtask import TaskAbortedError, VerificationAbortedError, ExtractionAbortedError

async def with_error_handling():
    wt = Webtask()
    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm)

    try:
        await agent.do("Add item to cart")
    except TaskAbortedError as e:
        print(f"Task failed: {e}")

    try:
        verdict = await agent.verify("cart has items")
    except VerificationAbortedError as e:
        print(f"Verification failed: {e}")

    try:
        price = await agent.extract("total price")
    except ExtractionAbortedError as e:
        print(f"Extraction failed: {e}")

    await wt.close()
```

## Using Bedrock

```python
from webtask.integrations.llm import Bedrock

async def with_bedrock():
    wt = Webtask()
    llm = Bedrock(model="us.anthropic.claude-haiku-4-5-20251001-v1:0", region="us-east-1")
    agent = await wt.create_agent(llm=llm)

    await agent.goto("https://google.com")
    await agent.do("Search for web automation")

    await wt.close()

asyncio.run(with_bedrock())
```

## Integration with Existing Browser

```python
from playwright.async_api import async_playwright

async def with_existing_browser():
    wt = Webtask()
    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        agent = await wt.create_agent_with_browser(llm=llm, browser=browser)

        await agent.goto("practicesoftwaretesting.com")
        await agent.do("Add 2 screws to the cart")

        await browser.close()

asyncio.run(with_existing_browser())
```

## More Examples

See the [examples directory](https://github.com/steve-z-wang/webtask/tree/main/examples) for Jupyter notebooks and additional examples.
