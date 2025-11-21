
# LLM

## Gemini

```python
from webtask.integrations.llm import Gemini
import os

llm = Gemini(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

agent = await wt.create_agent(llm=llm)
```

Available models: `gemini-2.5-flash`, `gemini-2.5-pro`

## Bedrock

```python
from webtask.integrations.llm import Bedrock

llm = Bedrock(
    model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    region="us-east-1"
)

agent = await wt.create_agent(llm=llm)
```

## Custom LLM

To use your own model, implement the `LLM` base class:

```python
from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage
from webtask.llm.tool import Tool
from typing import List

class CustomLLM(LLM):
    async def call_tools(
        self,
        messages: List[Message],
        tools: List[Tool],
    ) -> AssistantMessage:
        # Your implementation here
        # Convert messages to your API format
        # Call your LLM API
        # Convert response to AssistantMessage
        pass

# Use it
llm = CustomLLM()
agent = await wt.create_agent(llm=llm)
```

