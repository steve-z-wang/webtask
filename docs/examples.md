# Examples

## Complete Workflow

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import Gemini
from pydantic import BaseModel

class CartSummary(BaseModel):
    item_count: int
    total_price: float

async def main():
    wt = Webtask()
    agent = await wt.create_agent(
        llm=Gemini(model="gemini-2.5-flash"),
        wait_after_action=1.0,  # Adjust for slower sites
    )

    # Navigate first
    await agent.goto("https://practicesoftwaretesting.com")
    await agent.wait(3)

    # do() - Execute tasks
    await agent.do("Add 2 Flat-Head Wood Screws to the cart")
    await agent.do("Add 5 Cross-head screws to the cart")
    await agent.do("Go to the cart page")

    # extract() - Get structured data
    summary = await agent.extract("cart summary", CartSummary)
    print(f"Items: {summary.item_count}, Total: ${summary.total_price}")

    # verify() - Check conditions
    verdict = await agent.verify("the cart contains 7 items")
    if verdict:
        print("Cart verified!")

    await wt.close()

asyncio.run(main())
```

## Element Selection

Use `select()` to find elements with natural language and interact with them directly:

```python
async def form_example():
    wt = Webtask()
    agent = await wt.create_agent(
        llm=Gemini(model="gemini-2.5-flash"),
        wait_after_action=1.0,
    )

    await agent.goto("https://practicesoftwaretesting.com")
    await agent.wait(3)

    # Select and use the search input
    search_input = await agent.select("the search input field")
    await search_input.fill("screws")

    # Select and click the search button
    search_btn = await agent.select("the search button")
    await search_btn.click()

    await agent.wait(2)

    # Select the first product
    product = await agent.select("the first product in the list")
    await product.click()

    await wt.close()
```

## Error Handling

```python
from webtask import TaskAbortedError

try:
    await agent.do("Add item to cart")
except TaskAbortedError as e:
    print(f"Task failed: {e}")

try:
    verdict = await agent.verify("cart has items")
except TaskAbortedError as e:
    print(f"Verification failed: {e}")

try:
    price = await agent.extract("total price")
except TaskAbortedError as e:
    print(f"Extraction failed: {e}")
```

## Integration with Existing Browser

```python
from playwright.async_api import async_playwright
from webtask.integrations.llm import Gemini

async def with_existing_browser():
    wt = Webtask()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        agent = await wt.create_agent_with_browser(
            llm=Gemini(model="gemini-2.5-flash"),
            browser=browser,
            wait_after_action=1.0,
        )

        await agent.goto("https://practicesoftwaretesting.com")
        await agent.wait(3)
        await agent.do("add 2 screws to the cart")

        await browser.close()

asyncio.run(with_existing_browser())
```

## More Examples

See the [examples directory](https://github.com/steve-z-wang/webtask/tree/main/examples) for Jupyter notebooks.
