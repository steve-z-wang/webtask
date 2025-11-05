
# Examples

Complete code examples for common use cases.


## E-commerce Cart

```python
async def add_to_cart():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm, action_delay=1.5)

    result = await agent.execute(
        "Go to example-shop.com, find a blue shirt, add it to cart"
    )

    if result.completed:
        print("Item added to cart!")
        await agent.screenshot("cart.png")

    await wt.close()

asyncio.run(add_to_cart())
```


## Multi-Page Navigation

```python
async def multiple_tabs():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    # First page
    await agent.navigate("https://google.com")

    # Open second page
    page2 = await agent.open_page()
    agent.set_page(1)  # Switch to second page
    await agent.navigate("https://github.com")

    # Switch back to first page
    agent.set_page(0)
    await agent.execute("search for 'web automation'")

    # List all pages
    pages = agent.get_pages()
    print(f"Total pages: {len(pages)}")

    # Close second page
    await agent.close_page(1)

    await wt.close()

asyncio.run(multiple_tabs())
```


## Using OpenAI Instead of Gemini

```python
from webtask.integrations.llm import OpenAILLM

async def with_openai():
    wt = Webtask(headless=False)

    # Use GPT-4 Vision
    llm = OpenAILLM.create(model="gpt-4o")

    agent = await wt.create_agent(llm=llm)

    result = await agent.execute("Go to google.com and search for AI news")

    await wt.close()

asyncio.run(with_openai())
```


## Error Handling

```python
async def with_error_handling():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    try:
        result = await agent.execute(
            "Go to example.com and click the non-existent button",
            max_steps=5
        )

        if not result.completed:
            print("Task did not complete successfully")
            print(f"Completed {len(result.steps)} steps")

            # Save screenshot for debugging
            await agent.screenshot("error.png")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await wt.close()

asyncio.run(with_error_handling())
```


## More Examples

See the `examples/` directory in the GitHub repository:
- [tool_website_demo.ipynb](https://github.com/steve-z-wang/webtask/blob/main/examples/tool_website_demo.ipynb) - Jupyter notebook demonstration
- [google_search.ipynb](https://github.com/steve-z-wang/webtask/blob/main/examples/google_search.ipynb) - Google search example
- [existing_browser_integration.py](https://github.com/steve-z-wang/webtask/blob/main/examples/existing_browser_integration.py) - Connect to existing browser

