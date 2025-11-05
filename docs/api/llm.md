
# LLM Classes

webtask supports multiple LLM providers for multimodal reasoning.


## OpenAILLM

OpenAI GPT integration with multimodal support.

### `create()`

```python
@staticmethod
def create(
    model: str = "gpt-4o",
    api_key: str = None
) -> OpenAILLM
```

Create OpenAI LLM instance.

**Parameters:**
- `model` (str): Model name. Default: `"gpt-4o"`
- `api_key` (str): API key. If None, uses `OPENAI_API_KEY` environment variable

**Returns:** OpenAILLM instance

**Example:**
```python
from webtask.integrations.llm import OpenAILLM

# Using environment variable
llm = OpenAILLM.create(model="gpt-4o")

# With explicit API key
llm = OpenAILLM.create(
    model="gpt-4o-mini",
    api_key="your-api-key"
)
```

### Available Models

- **`gpt-4o`** - Recommended, multimodal, good balance of speed and capability
- **`gpt-4o-mini`** - Faster, cheaper, good for simple tasks

### Setup

```bash
export OPENAI_API_KEY="your-api-key"
```


## Choosing an LLM

| Provider | Model | Speed | Cost | Best For |
|----------|-------|-------|------|----------|
| Gemini | gemini-2.5-flash | Fast | Low | General use, quick tasks |
| Gemini | gemini-2.5-pro | Medium | Medium | Complex reasoning |
| OpenAI | gpt-4o | Medium | Medium | Balanced performance |
| OpenAI | gpt-4o-mini | Fast | Low | Simple tasks, high volume |

**Recommendation:** Start with **gemini-2.5-flash** for cost-effectiveness, upgrade to **gpt-4o** or **gemini-2.5-pro** if you need better reasoning.

