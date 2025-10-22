
# %% 

!pip install -e .

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
await input.fill("What is the capital of France?")
# %%
