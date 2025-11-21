# Examples

## Shopping Cart

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import Gemini
import os

async def main():
    wt = Webtask()

    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm)

    await agent.goto("https://practicesoftwaretesting.com/")

    await agent.do("Add 2 Flat-Head Wood Screws to the cart")
    await agent.do("Add 5 Cross-head screws to the cart")

    verdict = await agent.verify("the cart contains 7 items")
    if verdict:
        print("Cart verified!")

    await wt.close()

asyncio.run(main())
```

## Structured Output

```python
from pydantic import BaseModel

class ProductInfo(BaseModel):
    name: str
    price: float
    in_stock: bool

async def extract_product():
    wt = Webtask()

    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    agent = await wt.create_agent(llm=llm)

    await agent.goto("https://practicesoftwaretesting.com/")

    result = await agent.do(
        "Extract information about the first product",
        output_schema=ProductInfo
    )

    print(f"{result.output.name}: ${result.output.price}")
    await wt.close()

asyncio.run(extract_product())
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

        await agent.goto("https://practicesoftwaretesting.com/")
        await agent.do("Add 2 screws to the cart")

        await browser.close()

asyncio.run(with_existing_browser())
```

## More Examples

See the [examples directory](https://github.com/steve-z-wang/webtask/tree/main/examples) for Jupyter notebooks and additional examples.
