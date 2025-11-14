# Architecture

Understanding how webtask works internally.

## System Overview

```
┌──────────────────────────────────────────────────┐
│                    Webtask                       │
│              (Browser Manager)                   │
└─────────────────────┬────────────────────────────┘
                      │ creates
                      ↓
┌──────────────────────────────────────────────────┐
│                    Agent                         │
│          • execute(task) ← User calls this       │
│          • navigate(), select()                  │
└─────────────────────┬────────────────────────────┘
                      │
                      ↓
┌──────────────────────────────────────────────────┐
│                TaskExecutor                      │
│         Orchestrates Worker-Verifier loop        │
└──────────────────────────────────────────────────┘
             │
             ↓
      ┌──────────────┐
      │   Worker     │
      │  (Execute    │
      │   Actions)   │
      └──────┬───────┘
             │
             │ complete_work
             ↓
      ┌──────────────┐
      │   Verifier   │
      │  (Check &    │
      │   Decide)    │
      └──────┬───────┘
             │
             ├─ complete_task → DONE ✓
             ├─ abort_task → FAILED ✗
             └─ request_correction → back to Worker
```

## Worker-Verifier Pattern

When you call `agent.execute(task)`, the system uses a simple two-role pattern:

### Worker
- **Role**: Execute browser actions to complete the task
- **Input**: Task description, current page state
- **Output**: Action results, final page state
- **Tools**: navigate, click, fill, type, upload, wait, complete_work, abort_work
- **Conversation-based**: Maintains conversation history, continues on corrections

### Verifier
- **Role**: Check if task succeeded, request corrections if needed
- **Input**: Task description, worker summary, final page state
- **Output**: Decision (complete/correct/abort), feedback
- **Tools**: observe, wait, complete_task, request_correction, abort_task
- **Conversation-based**: Maintains separate conversation history

### Correction Loop
1. Worker executes task → complete_work
2. Verifier checks result
3. If incorrect: Verifier provides feedback → Worker retries (max 3 attempts)
4. If correct: Task complete
5. If impossible: Abort

## Conversation-Based Interface

Both Worker and Verifier use standard LLM conversation format:

**Message types:**
- SystemMessage: Role instructions
- UserMessage: Task + observations (DOM + screenshot)
- AssistantMessage: Tool calls from LLM
- ToolResultMessage: Execution results + new observations

**Context management:**
- Worker keeps last 2 observations
- Verifier keeps last 1 observation
- Tagged content filtering prevents unbounded growth

## Multimodal Context

The agent sees both text and visual context:

1. **Text context**: Filtered DOM tree with element IDs
2. **Visual context**: Screenshot with bounding boxes around interactive elements

This multimodal approach improves accuracy for complex UIs.

## Element Selection

**High-level**: `agent.select("search box")`

1. Agent captures page state (DOM + screenshot)
2. LLM sees element IDs in text + bounding boxes in image
3. LLM returns element ID
4. Agent maps element ID → XPath
5. Browser selects element using XPath

**Low-level**: Element selection happens automatically during autonomous execution

## XPath from Original DOM

Important implementation detail:
- **Shown to LLM**: Filtered DOM (only interactive/visible elements)
- **Used for selection**: XPath computed from original unfiltered DOM
- This ensures XPath matches the actual browser state

## Direct Control Mode

When you use `agent.navigate()` and `agent.select()`, you bypass the autonomous loop and directly control the browser:

```python
# Direct control - you decide the steps
await agent.navigate("https://example.com")
search = await agent.select("search box")
await search.fill("cats")
button = await agent.select("search button")
await button.click()
```

## Extension Points

### Custom LLM

Implement the `LLM` abstract class:

```python
from webtask.llm import LLM

class MyCustomLLM(LLM):
    async def call_tools(self, messages, tools):
        # For Worker/Verifier (tool calling)
        pass

    async def generate_response(self, messages, response_model):
        # For structured JSON output
        pass
```

### Custom Browser

Implement the `Browser`, `Session`, `Page`, and `Element` abstract classes:

```python
from webtask.browser import Browser, Session, Page, Element

class MyCustomBrowser(Browser):
    # Implement abstract methods
    pass
```

## More Details

For detailed internal architecture, see `CLAUDE.md` in the repository root.
