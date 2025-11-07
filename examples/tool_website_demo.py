# %% [markdown]
# # Webtask Demo: E-commerce Shopping Cart
#
# This notebook demonstrates automated web interaction using Webtask to add items to a shopping cart.

# %% [markdown]
# ## 1. Setup
#
# Install dependencies and import required libraries.

# %%
# !pip install -e ..

# %%
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# %% [markdown]
# ## 2. Initialize Webtask Agent
#
# Create a Webtask instance and configure the LLM.

# %%
from webtask import Webtask
from webtask.integrations.llm.google import GeminiLLM

wt = Webtask()
# GeminiLLM will automatically read GOOGLE_API_KEY from environment
llm = GeminiLLM.create(model="gemini-2.5-flash")

# %%
# Create agent with 3 second delay between actions to allow pages to load
agent = await wt.create_agent(llm=llm, action_delay=3.0)

# %% [markdown]
# ## 3. Initial State
#
# Navigate to the website and capture the starting state.

# %%
# Navigate to the starting page first
await agent.navigate("https://practicesoftwaretesting.com/")
await agent.wait_for_idle()

# Take screenshot before starting the task
print("Screenshot BEFORE task execution:")
await agent.screenshot("before_task.png")

# Display screenshot (if running in VSCode or Jupyter)
try:
    from IPython.display import Image, display
    display(Image(filename="before_task.png", width=800))
except ImportError:
    print("Screenshot saved to before_task.png")

# %% [markdown]
# ## 4. Execute Task
#
# Run the agent autonomously to add items to the shopping cart and print the complete result.

# %%
# Execute the task autonomously
print("Executing task...")

task = await agent.execute(
    "add 2 Flat-Head Wood Screws and 5 cross-head screws to the cart, and proceed to the cart",
    max_cycles=10
)

# Print detailed execution summary
print(task)

# Save execution summary to file
with open("task_execution_log.txt", "w") as f:
    f.write(str(task))
print("\nExecution log saved to task_execution_log.txt")

# %% [markdown]
# ## 5. Final State
#
# Capture the final state after task completion.

# %%
# Take screenshot after task completion
print("Screenshot AFTER task execution:")
await agent.screenshot("after_task.png")

# Display screenshot (if running in VSCode or Jupyter)
try:
    from IPython.display import Image, display
    display(Image(filename="after_task.png", width=800))
except ImportError:
    print("Screenshot saved to after_task.png")

# %%
