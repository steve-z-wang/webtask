# Using Custom LLM

You can use any LLM by implementing the `LLM` base class.

## Basic Implementation

```python
from webtask.llm import LLM
from webtask.llm.message import Message, AssistantMessage, TextContent
from webtask.llm.tool import Tool, ToolCall
from typing import List

class CustomLLM(LLM):
    def __init__(self, api_key: str, model: str):
        super().__init__()
        self.api_key = api_key
        self.model = model
        # Initialize your LLM client here

    async def call_tools(
        self,
        messages: List[Message],
        tools: List[Tool],
    ) -> AssistantMessage:
        # 1. Convert messages to your API format
        api_messages = self._convert_messages(messages)

        # 2. Convert tools to your API format
        api_tools = self._convert_tools(tools)

        # 3. Call your LLM API
        response = await your_llm_api.generate(
            messages=api_messages,
            tools=api_tools,
        )

        # 4. Convert response to AssistantMessage
        return self._convert_response(response)

    def _convert_messages(self, messages: List[Message]) -> list:
        # Convert webtask messages to your API format
        pass

    def _convert_tools(self, tools: List[Tool]) -> list:
        # Convert webtask tools to your API format
        pass

    def _convert_response(self, response) -> AssistantMessage:
        # Convert your API response to AssistantMessage
        # Return AssistantMessage with tool_calls
        pass
```

## Using Your Custom LLM

```python
from webtask import Webtask

wt = Webtask()
llm = CustomLLM(api_key="your-key", model="your-model")
agent = await wt.create_agent(llm=llm)

await agent.goto("https://example.com")
await agent.do("Click the login button")
```

## Reference Implementation

See the Gemini implementation for a complete example:

```
src/webtask/integrations/llm/google/gemini.py
```
