
# Architecture

Understanding how webtask works internally.


## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Webtask                          │
│                  (Browser Manager)                      │
└────────────────────┬────────────────────────────────────┘
                     │ creates
                     ↓
┌─────────────────────────────────────────────────────────┐
│                         Agent                           │
│              (User-facing Interface)                    │
│  • execute() - autonomous                               │
│  • run_step() - step-by-step                           │
│  • navigate(), select() - imperative                    │
└────────────────────┬────────────────────────────────────┘
                     │ uses
                     ↓
┌─────────────────────────────────────────────────────────┐
│                      LLMBrowser                         │
│           (Element ID ↔ XPath mapping)                  │
│  • Builds context for LLM                               │
│  • Maps element IDs to browser elements                 │
│  • Executes actions via XPath                           │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌──────────────┐          ┌──────────────┐
│ DOM Processing│          │   Browser    │
│  (Filtering,  │          │ (Playwright) │
│ Serialization)│          │              │
└──────────────┘          └──────────────┘
```


## Agent Roles

### BaseRole

Abstract base class with two methods:

```python
class BaseRole:
    async def propose_actions(self) -> Proposal:
        """Thinking phase - decide what to do"""
        pass

    async def execute(self, actions) -> List[ExecutionResult]:
        """Doing phase - execute actions"""
        pass
```

### ProposerRole

**Purpose:** Propose browser actions to advance task

**Tools available:**
- `navigate(url)`
- `click(element_id)`
- `fill(element_id, value)`
- `type(element_id, text)`
- `upload(element_id, file_path)`

### VerifierRole

**Purpose:** Check if task is complete

**Tools available:**
- `mark_complete(reason)` - Signal task completion


## Multimodal Context

By default, LLM receives both:

### Text Context
- Cleaned DOM tree in markdown format
- Element IDs for each interactive element
- Hierarchy preserved

### Visual Context
- Screenshot of current page
- Bounding boxes drawn around interactive elements
- Labels showing element IDs

This dual context significantly improves accuracy compared to text-only approaches.


## Design Patterns

### 1. Lazy Initialization

Browser launches only when first agent is created:

```python
wt = Webtask()  # No browser yet
agent = await wt.create_agent(llm)  # Browser launches here
```

### 2. Pure Functions

`WebContextBuilder.build_context()` is stateless:
- Takes page and config
- Returns string and element map
- No side effects
- Framework-agnostic

### 3. Metadata Preservation

`add_node_reference.py` preserves original nodes through filtering:
- Filtered tree: clean for LLM
- Original references: correct XPath
- Best of both worlds

### 4. Tool Registry

Each role has its own tool registry:
- ProposerRole: browser actions
- VerifierRole: completion check
- Type-safe with Pydantic schemas


## Task Execution Loop

```
┌─────────────────────────────────────┐
│ 1. Agent creates Task (owns state)  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. TaskExecutor receives Task       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. Select role (Proposer/Verifier)  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Role.propose_actions() → LLM     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. Role.execute(actions) → Browser  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 6. Create Step (proposal + results) │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 7. Record step in task history      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 8. Transition to next mode          │
└──────────────┬──────────────────────┘
               ↓
         Repeat or Done
```


## Next Steps

- Review [Examples](examples.md) to see architecture in action
- Read [API Reference](api/) for implementation details
- Check the [GitHub repository](https://github.com/steve-z-wang/webtask) for source code
