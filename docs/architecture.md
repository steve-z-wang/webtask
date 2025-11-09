
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
│                    TaskExecutor                         │
│         (Orchestrates Planner→Worker→Verifier)          │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │ Planner │  │ Worker  │  │ Verifier │
   │(Strategy)│  │(Execute)│  │ (Check)  │
   └─────────┘  └─────────┘  └──────────┘
```


## Planner→Worker→Verifier Loop

The core architecture implements an adaptive loop:

```
Loop until task complete:
  1. Planner: Plans NEXT subtask based on execution history
  2. Worker: Executes browser actions for the subtask
  3. Verifier: Checks if subtask succeeded AND if task complete
  4. Repeat with Planner adapting based on results
```

### Why This Architecture?

**Adaptive Planning:**
- Planner sees actual execution results before planning next step
- Can adjust strategy based on what actually happened
- Handles failures and unexpected page states gracefully

**Separation of Concerns:**
- **Planner**: Strategic thinking (WHAT to do next)
- **Worker**: Tactical execution (HOW to do it)
- **Verifier**: Validation (IS it done correctly?)

**Industry-Aligned:**
- Matches ReAct, Reflexion, and modern agent patterns
- Proven approach for LLM-based task execution


## Agent Roles

### Planner

**Purpose:** Strategic planning without page access

**Tools:**
- `start_subtask(goal)` - Define next subtask to execute

**Context:**
- Task description
- Subtask queue status
- Previous verifier feedback
- **NO page context** (focuses on strategy)

**Example:**
```python
# Sees: "No subtasks yet"
Planner: start_subtask("Find flights from NYC to LA")

# Later sees: "Subtask complete: Found 5 flights"
Planner: start_subtask("Select cheapest flight under $400")
```

### Worker

**Purpose:** Execute browser actions for current subtask

**Tools:**
- `navigate(url)` - Go to URL
- `click(element_id)` - Click element
- `fill(element_id, value)` - Fill form field
- `type(element_id, text)` - Type into element
- `upload(element_id, file_path)` - Upload file
- `wait(seconds)` - Wait for page
- `mark_done_working()` - Signal completion

**Context:**
- Current subtask goal
- Page state (DOM + screenshot with bounding boxes)
- Previous iterations in this session

**Example:**
```python
# Subtask: "Find flights from NYC to LA"
Worker: navigate("https://airline.com")
Worker: click(element_id="search-flights")
Worker: fill(element_id="from", value="NYC")
Worker: fill(element_id="to", value="LA")
Worker: click(element_id="search-button")
Worker: mark_done_working()
```

### Verifier

**Purpose:** Check subtask success and task completion

**Tools:**
- `mark_subtask_complete(details)` - Subtask succeeded
- `mark_subtask_failed(reason)` - Subtask failed
- `mark_task_complete(details)` - Entire task done
- `wait(seconds)` - Wait for page to load

**Context:**
- Task description
- Current subtask description
- Worker's actions
- Page state (DOM + screenshot)

**Example:**
```python
# Sees worker filled search form and clicked search
Verifier: wait(2)  # Let results load
Verifier: mark_subtask_complete("Found 5 available flights")

# Later...
Verifier: mark_task_complete("Flight booked, confirmation number ABC123")
```


## Multimodal Context

By default, Worker and Verifier receive both:

### Text Context
- Cleaned DOM tree in markdown format
- Element IDs for each interactive element (button-0, input-1, etc.)
- Hierarchy preserved for understanding page structure

### Visual Context
- Screenshot of current page
- Bounding boxes drawn around interactive elements
- Labels showing element IDs matching text context

This dual context significantly improves accuracy compared to text-only approaches.


## Design Patterns

### 1. Lazy Initialization

Browser launches only when first agent is created:

```python
wt = Webtask()  # No browser yet
agent = await wt.create_agent(llm)  # Browser launches here
```

### 2. Single Source of Truth

Session and iteration numbers stored once in data classes:

```python
@dataclass
class Iteration:
    iteration_number: int  # Set once, used everywhere
    observation: str
    thinking: str
    tool_calls: List[ToolCall]
```

No enumerate calculations - just use `iteration.iteration_number`.

### 3. Metadata Preservation

Original DOM nodes preserved through filtering:
- Filtered tree: clean for LLM display
- Original references: correct XPath for browser
- `add_node_reference.py` maintains the link

### 4. Tool Registry

Each role has its own tool registry:
- Planner: planning tools (start_subtask)
- Worker: browser actions (navigate, click, etc.)
- Verifier: completion tools (mark_complete, mark_failed)
- Type-safe with Pydantic schemas


## Task Execution Flow

```
┌─────────────────────────────────────┐
│ 1. User: agent.execute(task)        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. Agent creates TaskExecution      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. TaskExecutor.run() starts loop   │
└──────────────┬──────────────────────┘
               ↓
       ┌───────┴───────┐
       │   Main Loop   │
       └───────┬───────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Planner: plan next subtask       │
│    - Sees execution history         │
│    - Decides strategic next step    │
│    - Creates subtask                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. Worker: execute subtask          │
│    - Gets page context              │
│    - Performs browser actions       │
│    - Signals when done              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 6. Verifier: check results          │
│    - Reviews worker actions         │
│    - Checks page state              │
│    - Marks subtask complete/failed  │
│    - Checks if task complete        │
└──────────────┬──────────────────────┘
               ↓
          Task done? ──No──> Loop back to step 4
               │
              Yes
               ↓
┌─────────────────────────────────────┐
│ 7. Return TaskResult to user        │
└─────────────────────────────────────┘
```


## Key Benefits

**Adaptivity:**
- Planner adjusts strategy based on actual results
- Can recover from failures and unexpected states
- No rigid upfront planning

**Robustness:**
- Each role has clear, focused responsibility
- Verifier catches mistakes before continuing
- Can retry failed subtasks with different approaches

**Debuggability:**
- Clear session and iteration numbering (1-indexed everywhere)
- Full execution history preserved
- Debug files match console output


## Next Steps

- Review [Examples](examples.md) to see architecture in action
- Read [API Reference](api/index.md) for implementation details
- Check the [GitHub repository](https://github.com/steve-z-wang/webtask) for source code
