
# Data Classes

Data structures returned by webtask methods.


## Step

Single step in task execution.

### Attributes

- **`proposal`** (Proposal): Proposed actions from the agent
- **`execution_results`** (List[ExecutionResult]): Results of executed actions

### Example

```python
step = await agent.run_step()

print(f"Proposed {len(step.proposal.actions)} actions")
print(f"Message: {step.proposal.message}")
print(f"Complete: {step.proposal.complete}")

for result in step.execution_results:
    status = "✓" if result.success else "✗"
    print(f"{status} {result.action.tool}: {result.message}")
```


## ExecutionResult

Result of executing an action.

### Attributes

- **`action`** (Action): The action that was executed
- **`success`** (bool): Whether action succeeded
- **`message`** (str): Result message

### Example

```python
step = await agent.run_step()

for result in step.execution_results:
    print(f"Action: {result.action.tool}")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")

    if not result.success:
        print("Action failed! Investigating...")
```


## Complete Example

```python
import asyncio
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

async def main():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    # Execute and get TaskResult
    result = await agent.execute("search google for cats", max_steps=10)

    # Check result
    print(f"\n=== Task Result ===")
    print(f"Completed: {result.completed}")
    print(f"Total steps: {len(result.steps)}")
    print(f"Message: {result.message}")

    # Inspect each step
    for i, step in enumerate(result.steps, 1):
        print(f"\n=== Step {i} ===")
        print(f"Agent reasoning: {step.proposal.message}")
        print(f"Actions proposed: {len(step.proposal.actions)}")

        # Show each action
        for action in step.proposal.actions:
            print(f"  - Tool: {action.tool}")

        # Show execution results
        for exec_result in step.execution_results:
            status = "✓" if exec_result.success else "✗"
            print(f"  {status} {exec_result.action.tool}: {exec_result.message}")

    await wt.close()

asyncio.run(main())
```

