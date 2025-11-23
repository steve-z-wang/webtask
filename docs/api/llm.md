
# LLM

## Gemini

```python
from webtask.integrations.llm import Gemini

llm = Gemini(model="gemini-2.5-flash")
agent = await wt.create_agent(llm=llm, mode="text")
```

## GeminiComputerUse

For visual mode with pixel-based interactions:

```python
from webtask.integrations.llm import GeminiComputerUse

llm = GeminiComputerUse(model="gemini-2.5-computer-use-preview")
agent = await wt.create_agent(llm=llm, mode="visual")
```

## Bedrock (WIP)

```python
from webtask.integrations.llm import Bedrock

llm = Bedrock(model="anthropic.claude-sonnet-4-20250514-v1:0")
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

