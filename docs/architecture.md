
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
│         Orchestrates hierarchical execution      │
└──────────────────────────────────────────────────┘
             │
             │ TASK LEVEL (max_cycles)
             │
             ↓
      ┌──────────────┐
      │   Manager    │──────────────────────┐
      │  (Plan &     │                      │
      │   Adjust)    │                      │ complete_task
      └──────┬───────┘                      │ or abort_task
             │                              │
             │ creates/adjusts              ↓
             │ subtask queue            [DONE]
             │
             │ SUBTASK LEVEL (for each pending subtask)
             │
             ├─────────────────────┐
             ↓                     │
      ┌──────────────┐             │
      │    Worker    │             │
      │  (Execute    │             │
      │   Actions)   │             │
      └──────┬───────┘             │
             │                     │
             │ mark_done_working   │
             ↓                     │
      ┌──────────────┐             │
      │   Verifier   │             │
      │  (Check &    │             │ request_reschedule
      │   Decide)    │─────────────┘ (back to Manager)
      └──────┬───────┘
             │
             ├─ complete_subtask → next subtask
             │
             └─ request_correction → retry Worker
```

## Manager→Worker→Verifier Hierarchy

When you call `agent.execute(task)`, a hierarchical execution system runs:

```
Task Level (max_cycles):
  For each manager cycle:
    1. Manager Session:
       - Reviews task and execution history
       - Plans/adjusts subtask queue
       - May call complete_task or abort_task

    2. Subtask Level:
       For each pending subtask:
         a. Worker Session:
            - Executes browser actions
            - Marks work complete

         b. Verifier Session:
            - Checks if subtask succeeded
            - May request_correction (retry worker)
            - May request_reschedule (back to manager)
            - Or complete_subtask

         c. If reschedule requested → break to next manager cycle

    3. Repeat manager cycle if subtasks remain
```

**Key points:**
- **Not a simple loop** - It's hierarchical with task-level and subtask-level execution
- **Manager** operates at task level, planning strategy
- **Worker/Verifier** operate at subtask level, executing and checking
- **Correction mechanism**: Verifier can request worker to retry
- **Adaptive replanning**: Verifier can send control back to Manager

### Manager
- **Role**: Strategic planning
- **Input**: Task description, execution history
- **Output**: Subtask queue
- **Tools**: `add_subtask`, `complete_task`, `abort_task`, `cancel_pending_subtasks`, `start_subtask`

### Worker
- **Role**: Execute browser actions
- **Input**: Current subtask, page state
- **Output**: Action results
- **Tools**: `navigate`, `click`, `fill`, `type`, `upload`, `wait`, `mark_done_working`

### Verifier
- **Role**: Check completion and request corrections
- **Input**: Subtask goal, page state, worker actions
- **Output**: Completion status or correction request
- **Tools**: `complete_subtask`, `request_correction`, `request_reschedule`

## Direct Control Mode

When you use `agent.navigate()` and `agent.select()`, you bypass the autonomous loop and directly control the browser with natural language selectors.

```python
# Direct control - you decide the steps
await agent.navigate("https://example.com")
search = await agent.select("search box")
await search.fill("cats")
button = await agent.select("search button")
await button.click()
```

## Multimodal Context

The agent sees both:
1. **Text context**: Filtered DOM tree with element IDs
2. **Visual context**: Screenshot with bounding boxes drawn around interactive elements

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

## Extension Points

### Custom LLM

Implement the `LLM` abstract class:

```python
from webtask.llm import LLM, Content

class MyCustomLLM(LLM):
    async def generate(self, messages: List[Content]) -> str:
        # Your implementation
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
