
# %%

!pip install -e .

# %%

import logging

# Enable DEBUG logging to see LLM API calls, prompts, and responses
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# %%

from webtask import Webtask
from webtask.integrations.llm.google import GeminiLLM

wt = Webtask()
llm = GeminiLLM.create(model="gemini-2.5-flash", temperature=0.3)


# %% 

agent = await wt.create_agent(
    llm=llm,
)


# %% 

await agent.navigate("google.com")

# %%

input = await agent.select("google search input")
await input.type("what is the capital of france?")
await agent.wait(2)

# %%


button = await agent.select("google search button")
await button.click()
await agent.wait(2)

# %%

button = await agent.select("recaptcha checkbox")
await button.click()
# %%
