# Scheduler-Worker-Verifier Architecture Design

## Overview

The new architecture uses three independent roles that communicate through tool calls:
- **Scheduler**: Plans work at a high level (no page access)
- **Worker**: Executes browser actions (full page access)
- **Verifier**: Checks completion and decides next steps (full page access)

Each role:
- Runs independently with its own `run() -> RoleResult` method
- Has an internal loop until it calls a transition tool
- Returns a result object with execution history
- Is fully decoupled from other roles

---

## Scheduler

### Purpose
Plans work at a high level without seeing the actual webpage. Can queue multiple work assignments when the task is clear.

### Context (what Scheduler sees)
- Task description (original user goal)
- Execution history (previous scheduler→worker→verifier cycles)
- Available resources (files for upload, etc.)
- Current work queue status
- **NO page context** (cannot see webpage)

### Tools
| Tool | Parameters | Description |
|------|-----------|-------------|
| `set_subtasks` | `subtasks: List[str]` | Replace entire subtask backlog |
| `add_subtask` | `subtask: str` | Append subtask to end of backlog |
| `insert_subtask` | `subtask: str, index: int` | Insert subtask at specific position |
| `delete_subtask` | `index: int` | Remove subtask at position |
| `update_subtask` | `index: int, subtask: str` | Modify subtask at position |
| `start_work` | - | Transition to Worker to begin executing subtasks |

### Example Behavior
```python
# Task: "Book a flight from NYC to LA"

# Initial planning
Scheduler: set_subtasks([
    "Find available flights from NYC to LA",
    "Select the cheapest flight under $400",
    "Complete booking form with passenger details"
])
Scheduler: start_work()  # Transitions to Worker

# Later, after verifier requests reschedule
# Scheduler sees: "Flights found but dates wrong"

Scheduler: set_subtasks([
    "Fix the departure date to next week",
    "Search again for flights",
    "Select the cheapest flight under $400",
    "Complete booking"
])
Scheduler: start_work()  # Transitions to Worker with updated plan

# Or just add one more subtask
Scheduler: add_subtask("Verify confirmation email received")
Scheduler: start_work()
```

### Return Type
```python
List[Iteration]  # All iterations until start_work called
```

---

## Worker

### Purpose
Executes browser actions based on assigned work instructions. Focused on tactical execution of current assignment.

### Context (what Worker sees)
- Current work assignment (from scheduler or verifier)
- Current page state (DOM + screenshot with bounding boxes)
- Recent context (2-3 previous work cycles for continuity)
  - Previous assignment
  - Previous result summary
- **NO full task history** (stays focused on current work)

### Tools
| Tool | Parameters | Description |
|------|-----------|-------------|
| `navigate` | `url: str` | Navigate to URL |
| `click` | `element_id: str` | Click element |
| `fill` | `element_id: str, value: str` | Fill form field |
| `type` | `element_id: str, text: str` | Type into element |
| `upload` | `element_id: str, resource_name: str` | Upload file |
| `wait` | `seconds: float` | Wait for duration |
| `mark_done` | `summary: str` | Report work completion, transition to Verifier |

### Example Behavior
```python
# Assignment: "Search for NYC to LA flights"

Worker: navigate("https://flights.com")
Worker: fill("from-input", "NYC")
Worker: fill("to-input", "LA")
Worker: click("search-button")
Worker: wait(2.0)
Worker: mark_done("Found 15 flights ranging from $299 to $850. Search results displayed.")
# Transitions to Verifier
```

### Return Type
```python
List[Iteration]  # All iterations until mark_done called
```

---

## Verifier

### Purpose
Checks if work completed successfully and decides next action. Can send worker back for corrections or request replanning from scheduler.

### Context (what Verifier sees)
- Original task goal
- Current work assignment (what worker was supposed to do)
- Worker's completion summary
- Current page state (DOM + screenshot)
- Full execution history (all cycles)

### Tools
| Tool | Parameters | Description |
|------|-----------|-------------|
| `mark_complete` | `reason: str` | Task fully complete, exit successfully |
| `continue_work` | `instructions: str` | Minor correction needed, back to Worker with new instructions |
| `request_reschedule` | `reason: str` | Need new plan, back to Scheduler |

### Example Behaviors

**Case 1: Work incomplete, minor fix**
```python
# Worker said: "Found flights"
# Verifier sees: Wrong dates selected

Verifier: continue_work("The dates are wrong. Go back and change departure to next week, then search again.")
# Transitions back to Worker
```

**Case 2: Work complete, but task not done**
```python
# Worker said: "Found 15 flights, cheapest is $299"
# Verifier sees: Flights displayed but nothing selected yet

Verifier: request_reschedule("Flights successfully found. Ready for next step: selection and booking.")
# Transitions back to Scheduler
```

**Case 3: Task fully complete**
```python
# Worker said: "Booking submitted"
# Verifier sees: Confirmation page with booking number

Verifier: mark_complete("Flight successfully booked. Confirmation number ABC123 visible on page.")
# Task exits successfully
```

### Return Type
```python
List[Iteration]  # Usually just one iteration (single check)
```

---

## Flow Diagram

```
┌─────────────┐
│  Scheduler  │ ← (initial entry)
│ (no page)   │
└──────┬──────┘
       │ assign_work() × N
       │ start_work()
       ↓
┌─────────────┐
│   Worker    │
│ (has page)  │
└──────┬──────┘
       │ navigate(), click(), fill()...
       │ mark_done()
       ↓
┌─────────────┐
│  Verifier   │
│ (has page)  │
└──────┬──────┘
       │
       ├─→ mark_complete() ───→ DONE ✓
       │
       ├─→ continue_work() ───→ back to Worker
       │
       └─→ request_reschedule() ───→ back to Scheduler
```

---

## Data Model

### Task
```python
@dataclass
class Task:
    description: str                    # Original user goal (top-level task)
    resources: Dict[str, str]           # Files available for upload
    subtasks: List[str]                 # Subtasks from scheduler
    current_subtask_index: int          # Current position in subtask queue
    execution_history: List[ExecutionCycle]
    max_steps: int = 10
```

### Iteration
```python
@dataclass
class Iteration:
    """One LLM call + tool executions within a role's run()"""
    role: str                   # "scheduler", "worker", "verifier"
    reasoning: str              # LLM's reasoning message
    tool_calls: List[ToolCall]  # Tools executed
    timestamp: datetime
```

### ToolCall
```python
@dataclass
class ToolCall:
    """Tool call with execution tracking"""
    tool: str
    parameters: Dict[str, Any]
    reason: str
    # Execution results
    success: Optional[bool]
    result: Optional[Any]
    error: Optional[str]
    timestamp: Optional[datetime]
```

### ProposedToolCall (LLM Schema)
```python
class ProposedToolCall(BaseModel):
    """What LLM returns (JSON-serializable)"""
    tool: str
    parameters: Dict[str, Any]
    reason: str
```

---

## TaskExecutor Flow

```python
class TaskExecutor:
    async def execute(self) -> TaskResult:
        current_role = "scheduler"

        while not complete:
            if current_role == "scheduler":
                result = await self.scheduler.run()
                # Check for start_work() tool call
                if has_tool(result, "start_work"):
                    current_role = "worker"

            elif current_role == "worker":
                result = await self.worker.run()
                # Check for mark_done() tool call
                if has_tool(result, "mark_done"):
                    current_role = "verifier"

            elif current_role == "verifier":
                result = await self.verifier.run()

                # Check decision
                if has_tool(result, "mark_complete"):
                    return TaskResult(completed=True, ...)
                elif has_tool(result, "continue_work"):
                    current_role = "worker"
                elif has_tool(result, "request_reschedule"):
                    current_role = "scheduler"
```

---

## Key Design Principles

1. **Separation of Concerns**
   - Scheduler: Strategic planning (no page access)
   - Worker: Tactical execution (full page access)
   - Verifier: Quality control (full page access)

2. **Decoupling**
   - Each role is independent
   - Communication only through tool calls
   - No role knows about others' internals

3. **OOP Encapsulation**
   - Each role returns its own result type
   - State encapsulated within roles
   - No global logger dependency

4. **Functional Pattern**
   - Roles are pure(ish): input context → result
   - Easy to test and debug
   - Explicit return values

5. **Flexibility**
   - Scheduler can queue multiple assignments
   - Verifier can redirect to worker or scheduler
   - Worker focuses only on current work
