# Using Cookies

## Load Cookies from File

```python
from webtask import Webtask
from webtask.integrations.llm import Gemini
import json
import os

# Load cookies from JSON file
with open("cookies.json", "r") as f:
    cookies = json.load(f)

wt = Webtask()
llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

# Create agent with cookies
agent = await wt.create_agent(llm=llm, cookies=cookies)

await agent.goto("https://example.com")
# You're already logged in!
```

## Cookie Format

Cookies should be a list of dictionaries with these fields:

```python
cookies = [
    {
        "name": "session_id",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
    }
]
```

## Save Cookies

```python
# Get cookies from agent's session
session = agent._browser._session
cookies = await session.get_cookies()

# Save to file
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=2)
```

## Use Case: Persistent Login

```python
import json
import os
from pathlib import Path

COOKIES_FILE = Path("session_cookies.json")

async def create_agent_with_session():
    wt = Webtask()
    llm = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

    # Load cookies if they exist
    cookies = None
    if COOKIES_FILE.exists():
        with open(COOKIES_FILE) as f:
            cookies = json.load(f)

    agent = await wt.create_agent(llm=llm, cookies=cookies)

    return agent, wt

async def save_session(agent):
    session = agent._browser._session
    cookies = await session.get_cookies()

    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)

# Usage
agent, wt = await create_agent_with_session()

await agent.goto("https://example.com")

# If not logged in, login
if not await agent.verify("user is logged in"):
    await agent.do("Login with email test@example.com and password pass123")
    await save_session(agent)  # Save cookies for next time

# Now you're logged in
await agent.do("Go to dashboard")

await wt.close()
```
