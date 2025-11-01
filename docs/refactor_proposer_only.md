# Refactor: Single-LLM-Call Architecture (Proposer-Only)

## Current Architecture (2 LLM Calls Per Step)

### Flow in `agent.run_step()`:

1. **Proposer** (LLM Call #1)
   - Input: task, step_history, tools, page_state
   - Output: `actions[]`
   - Prompt: `proposer_system`

2. **Executer** (No LLM)
   - Input: actions
   - Output: `execution_results[]`
   - Executes tools synchronously

3. **Wait** (No LLM)
   - Delay for page stabilization

4. **Verifier** (LLM Call #2)
   - Input: task, step_history, current_actions, current_execution_results, page_state
   - Output: `{complete: bool, message: str}`
   - Prompt: `verifier_system`

### Cost per step:
- **2 LLM calls** (proposer + verifier)
- For a 10-step task: **20 LLM calls total**

---

## Proposed Architecture (1 LLM Call Per Step)

### New Flow in `agent.run_step()`:

1. **Proposer** (LLM Call #1 - ONLY CALL)
   - Input: task, step_history (includes previous execution results), page_state
   - Output: `{complete: bool, message: str, actions: []}`
   - Prompt: `proposer_system` (updated to include verification logic)

2. **Executer** (No LLM)
   - Input: actions
   - Output: `execution_results[]`
   - Executes tools synchronously

3. **Wait** (No LLM)
   - Delay for page stabilization

### Cost per step:
- **1 LLM call** (proposer only)
- For a 10-step task: **10 LLM calls total** (50% reduction)

---

## Key Insight: Why This Works

The verifier currently checks completion AFTER the current step's execution. But the proposer can make the same determination BEFORE proposing the next actions by examining:

1. **Current page state** - Does the page show the task is complete?
2. **Previous step results** - Did the last actions succeed?
3. **Step history** - What has been accomplished so far?

### Example Flow:

**Step 1:**
- Proposer sees empty history, proposes: fill form fields
- Returns: `{complete: false, message: "Filling form", actions: [fill input-0, fill input-1]}`

**Step 2:**
- Proposer sees history showing fills succeeded
- Proposer sees current page with filled fields
- Proposes: click submit button
- Returns: `{complete: false, message: "Submitting form", actions: [click button-0]}`

**Step 3:**
- Proposer sees history showing submit succeeded
- Proposer sees current page showing success message
- No more actions needed
- Returns: `{complete: true, message: "Task completed: Form submitted successfully", actions: []}`

---

## Implementation Changes

### 1. Update `step.py`

```python
@dataclass
class ProposalResult:
    """Result from proposer including completion status and actions."""

    complete: bool
    message: str
    actions: List[Action]


@dataclass
class Step:
    """Represents one complete agent cycle."""

    proposal: ProposalResult  # Changed from proposals/verification
    executions: List[ExecutionResult]
```

### 2. Update `proposer.py`

```python
async def propose(self) -> ProposalResult:
    """Propose next actions and determine if task is complete."""
    context = await self._build_context()
    response = await self.llm.generate(context)
    data = parse_json(response)

    complete = data.get("complete")
    message = data.get("message")
    actions_list = data.get("actions", [])

    if complete is None or not message:
        raise ValueError("LLM response missing 'complete' or 'message'")

    # Parse actions (same as before)
    actions = []
    for action_dict in actions_list:
        # ... existing action parsing logic ...
        actions.append(Action(...))

    return ProposalResult(
        complete=bool(complete),
        message=message,
        actions=actions
    )
```

### 3. Update `agent.py`

```python
async def run_step(self) -> Step:
    """Execute one step of the current task."""
    from ..utils import wait

    if self.current_task is None or self.proposer is None:
        raise RuntimeError("No task set. Call set_task() first.")

    step_num = len(self.step_history.get_all()) + 1
    self.logger.debug(f"=== Starting Step {step_num} ===")

    # Phase 1: Propose actions AND check completion
    self.logger.debug("Phase 1: Proposing actions and checking completion...")
    proposal = await self.proposer.propose()
    self.logger.debug(f"Complete: {proposal.complete}")
    self.logger.debug(f"Message: {proposal.message}")
    self.logger.debug(f"Proposed {len(proposal.actions)} action(s)")

    # Phase 2: Execute actions (if any)
    exec_results = []
    if proposal.actions:
        self.logger.debug("Phase 2: Executing actions...")
        exec_results = await self.executer.execute(proposal.actions)

        # Wait for page to stabilize
        self.logger.debug(f"Phase 3: Waiting {self.action_delay}s...")
        await wait(self.action_delay)

    step = Step(proposal=proposal, executions=exec_results)
    self.step_history.add_step(step)

    self.logger.debug(f"=== Step {step_num} Complete ===\n")

    return step

async def execute(self, task: str, max_steps: int = 10, clear_history: bool = True) -> TaskResult:
    """Execute a task autonomously."""
    self.set_task(task, clear_history=clear_history)

    for i in range(max_steps):
        step = await self.run_step()

        # Check completion from proposal
        if step.proposal.complete:
            return TaskResult(
                completed=True,
                steps=self.step_history.get_all(),
                message=step.proposal.message,
            )

    return TaskResult(
        completed=False,
        steps=self.step_history.get_all(),
        message=f"Task not completed after {max_steps} steps",
    )

def set_task(self, task: str, clear_history: bool = True) -> None:
    """Set current task for step-by-step execution."""
    self.current_task = task

    if clear_history:
        self.step_history.clear()

    # Only create proposer and executer (no verifier)
    self.proposer = Proposer(
        self.llm, task, self.step_history, self.tool_registry, self.llm_browser
    )
    self.executer = Executer(self.tool_registry, self.action_delay)
```

### 4. Update `step_history.py`

```python
def to_context_block(self) -> Block:
    """Convert step history to context block for LLM."""
    if not self._steps:
        return Block("Step History:\nNo steps executed yet.")

    lines = ["Step History:"]
    for i, step in enumerate(self._steps, 1):
        lines.append("")
        lines.append(f"Step {i}:")

        # Show completion status and message
        lines.append(f"  Status: {'Complete' if step.proposal.complete else 'Incomplete'}")
        lines.append(f"  Message: {step.proposal.message}")

        # Show actions and execution results
        for j, (action, execution) in enumerate(
            zip(step.proposal.actions, step.executions), 1
        ):
            lines.append(f"  Action {j}:")
            lines.append(f"    Tool: {action.tool_name}")
            lines.append(f"    Reason: {action.reason}")
            lines.append(f"    Parameters: {action.parameters}")
            lines.append(
                f"    Execution: {'Success' if execution.success else 'Failed'}"
            )
            if execution.error:
                lines.append(f"    Error: {execution.error}")

    return Block("\n".join(lines))
```

### 5. Update Prompt: `proposer_system`

```yaml
proposer_system:
  description: "System prompt for the Proposer agent"
  content: |
    You are a web automation agent. Your task is to propose the next actions AND determine if the task is complete.

    You will receive:
    - The task to accomplish
    - Step history (previous actions and results)
    - Available tools and their schemas
    - Current page state with element IDs

    You must respond with a JSON object containing:
    {
      "complete": true/false,
      "message": "Explanation of task status",
      "actions": [
        {
          "reason": "Why you're taking this action",
          "tool": "tool_name",
          "parameters": {...}
        },
        ...
      ]
    }

    ## Decision Flow

    **FIRST: Check if task is complete**
    1. Re-read the original task - What EXACTLY was requested?
    2. Check current page state - Does it show the task is done?
    3. Review step history - Were previous actions successful?
    4. Verify ALL requirements - Is every part of the task satisfied?

    **THEN: Decide on actions**
    - If complete=true: Return empty actions []
    - If complete=false: Return next actions to take

    ## When to Mark Complete (complete: true)

    Mark complete ONLY when:
    - ALL requirements of the task are satisfied
    - Current page state confirms completion
    - Previous actions succeeded (check step history)
    - No further steps needed

    Return: `{"complete": true, "message": "Success explanation", "actions": []}`

    ## When to Mark Incomplete (complete: false)

    Mark incomplete when:
    - Task has more steps remaining
    - Some requirements not yet satisfied
    - Previous actions failed and need retry
    - Page needs more interaction

    Return: `{"complete": false, "message": "What still needs to be done", "actions": [...]}`

    ## Action Planning (when complete=false)

    1. Review current page state - What elements are visible NOW?
    2. Check step history - Don't repeat failed actions
    3. Plan efficiently - Multiple actions per step is OK
    4. Use exact element IDs from page context

    ## Important Rules

    - Only use element IDs from current page context
    - Only use available tools from tools list
    - Provide clear reasoning for each action
    - Check execution results in history
    - Be thorough when checking completion
    - Return empty actions when complete=true

    ## Response Format

    Task complete:
    ```json
    {
      "complete": true,
      "message": "Task completed: Form submitted successfully",
      "actions": []
    }
    ```

    Task incomplete:
    ```json
    {
      "complete": false,
      "message": "Need to fill remaining fields and submit form",
      "actions": [
        {"reason": "Fill price field", "tool": "fill", "parameters": {"element_id": "input-0", "value": "50"}},
        {"reason": "Submit form", "tool": "click", "parameters": {"element_id": "button-0"}}
      ]
    }
    ```
```

### 6. Delete `verifier.py`

No longer needed - verification logic is now in proposer.

---

## Migration Steps

1. **Create new data structures** in `step.py`:
   - Add `ProposalResult` dataclass
   - Update `Step` to use `proposal: ProposalResult`

2. **Update `proposer.py`**:
   - Change return type from `List[Action]` to `ProposalResult`
   - Parse `complete` and `message` from LLM response
   - Update prompt reference to new `proposer_system`

3. **Update `agent.py`**:
   - Remove verifier creation in `set_task()`
   - Update `run_step()` to use `proposal.complete`
   - Update `execute()` to check `step.proposal.complete`
   - Remove verifier phase from loop

4. **Update `step_history.py`**:
   - Change `to_context_block()` to use `step.proposal`

5. **Update prompt** in `prompts_data/agent/proposer.yaml`:
   - Add verification logic
   - Add `complete` and `message` to response schema
   - Add decision flow guidance

6. **Delete files**:
   - `src/webtask/agent/role/verifier.py`
   - `src/webtask/prompts_data/agent/verifier.yaml`

7. **Update tests**:
   - Update test expectations for new `Step` structure
   - Update test mocks for proposer response format

---

## Benefits

1. **50% reduction in LLM calls** - Huge cost savings
2. **Faster execution** - Less latency per step
3. **Simpler architecture** - One role instead of two
4. **Same capabilities** - Proposer has all context needed for verification
5. **More coherent** - Single LLM makes both planning and verification decisions

## Risks / Considerations

1. **Prompt complexity** - Proposer prompt becomes more complex (but manageable)
2. **Potential for confusion** - LLM must do two tasks (but they're related)
3. **Testing needed** - Need to verify completion detection works well

## Recommendation

**Proceed with refactor.** The benefits (50% cost reduction, faster execution) far outweigh the risks. The proposer already has all the context it needs to determine completion, and combining these roles is more coherent than separating them.
