# Refactor Plan: Worker-Only Architecture with persist_context

## Goal
Simplify from Worker/Verifier to single Worker with optional persistent context.

## Architecture Change

**Before:**
```
Agent.execute(task)
  → TaskExecutor (orchestrates loop)
    → Worker (proposes actions)
    → Verifier (checks completion)
```

**After:**
```
Agent.do(task, max_steps=20)
  → Worker.do(task, previous_session, max_steps) (stateless)
  → Returns WorkerSession (internal)
  → Agent converts to simple result (user-facing)
  → Agent manages session if persist_context=True
```

## Worker Interface

```python
class WorkerStatus(str, Enum):
    """Worker execution status."""
    COMPLETED = "completed"
    ABORTED = "aborted"
    MAX_STEPS = "max_steps"


@dataclass
class WorkerSession:
    """Worker session - execution result + conversation history."""

    # Execution result
    status: WorkerStatus
    output: Optional[Any]  # Structured data from set_output
    feedback: str  # Summary of what happened

    # Conversation history (for persist_context)
    pairs: List[ToolCallPair]  # Full conversation (LLM calls + results)

    # Metadata
    task_description: str
    steps_used: int
    max_steps: int

    # Optional debug info
    final_dom: Optional[str] = None
    final_screenshot: Optional[str] = None


class Worker:
    async def do(
        self,
        task: str,
        previous_session: Optional[WorkerSession] = None,
        max_steps: int = 20
    ) -> WorkerSession:
        """
        Execute task, optionally continuing from previous session.

        Returns WorkerSession with execution result and conversation history.
        """
```

```python
class Agent:
    def __init__(self, llm, context, persist_context=False):
        self.persist_context = persist_context
        self.last_session = None  # WorkerSession if persist_context=True

    async def do(self, task: str, max_steps: int = 20) -> dict:
        """
        Public API - returns simple user-facing result.
        """
        worker = Worker(llm, session_browser)

        if self.persist_context:
            session = await worker.do(task, self.last_session, max_steps)
            self.last_session = session
        else:
            session = await worker.do(task, None, max_steps)

        # Convert WorkerSession → simple result
        return {
            "status": session.status,
            "output": session.output,
            "feedback": session.feedback
        }
```

## Phases

### PHASE 1: Update Worker interface (stateless with session parameter)
- Rename `Worker.run()` → `Worker.do()`
- Add `previous_session` parameter
- Add `max_steps` parameter to `do()`
- Keep backward compatible (existing code still works)

**Files:**
- `src/webtask/_internal/agent/worker/worker.py` - update interface
- `src/webtask/_internal/agent/worker/worker_session.py` - ensure it's reusable

### PHASE 2: Add persist_context to Agent
- Add `persist_context` bool parameter to Agent.__init__
- Agent stores `self.history_pairs = []` if persist_context=True
- Pass history to Executor.run()
- Update history after each run

**Files:**
- `src/webtask/agent/agent.py` - add persist_context logic

### PHASE 3: Remove Verifier and old TaskExecutor
- Delete `verifier/` folder
- Delete `task_executor.py`
- Delete `verifier_prompt.py`
- Update Agent to only use Executor (no TaskExecutor)

**Files to delete:**
- `src/webtask/_internal/agent/verifier/`
- `src/webtask/_internal/agent/task_executor.py`
- `src/webtask/_internal/prompts/verifier_prompt.py`

### PHASE 4: Rename execute() → do() and remove select()
- Rename `Agent.execute()` → `Agent.do()`
- Remove `Agent.select()` method
- Update all examples

**Files:**
- `src/webtask/agent/agent.py`
- `examples/`

### PHASE 5: Update tests and docs
- Fix all tests to use new API
- Update README, CLAUDE.md
- Update docstrings

**Files:**
- `tests/`
- `README.md`
- `CLAUDE.md`
- `docs/`

## Key Decisions

1. **Executor is stateless** - history managed by Agent
2. **Method names:**
   - Internal: `executor.run(task, history)`
   - Public: `agent.do(task)`
3. **Backward compatibility** - Phases 1-2 don't break existing code
4. **Breaking changes** - Phases 3-4 require test updates

## Testing Checkpoints

- ✅ Phase 1 COMPLETE: WorkerSession updated, Worker.run() → Worker.do()
- ✅ Phase 2 COMPLETE: Agent.persist_context added, manages last_session
- ✅ Phase 3 COMPLETE: Verifier and TaskExecutor removed
- ✅ Phase 4 COMPLETE: Agent.select() method removed
- ⚠️ Phase 5 TODO: Update tests and documentation

## Implementation Status

**COMPLETED:**
- ✅ WorkerSession redesigned with WorkerStatus enum (COMPLETED, ABORTED, MAX_STEPS)
- ✅ Worker.do(task, previous_session, max_steps) interface implemented
- ✅ Worker is stateless - accepts and returns WorkerSession
- ✅ Agent.do() method added with persist_context support
- ✅ Agent stores last_session when persist_context=True
- ✅ Verifier folder deleted
- ✅ TaskExecutor deleted
- ✅ verifier_prompt.py deleted
- ✅ Agent.select() removed
- ✅ selector_llm parameter removed from Agent.__init__

**REMAINING:**
- Update all tests to use new Agent.do() API
- Update examples to use new API
- Update README.md and CLAUDE.md documentation
