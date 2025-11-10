
# Data Classes

Data structures returned by webtask methods.

## TaskExecution

Returned by `agent.execute()`. Contains the complete execution state of a task.

```python
@dataclass
class TaskExecution:
    task: Task
    history: List[Union[ManagerSession, SubtaskExecution]]
    subtask_queue: SubtaskQueue
    status: TaskStatus
    failure_reason: str | None
```

**Fields:**
- `task`: The original task definition with description and resources
- `history`: List of all manager sessions and subtask executions
- `subtask_queue`: Queue of subtasks (pending, in-progress, completed)
- `status`: Current task status (IN_PROGRESS, COMPLETED, or ABORTED)
- `failure_reason`: Explanation if task was aborted (None otherwise)

**Methods:**
- `__str__()`: Returns formatted summary of execution

**Example:**
```python
from webtask import TaskStatus

result = await agent.execute("search for cats")

# Check status
if result.status == TaskStatus.COMPLETED:
    print("Task completed successfully!")
elif result.status == TaskStatus.ABORTED:
    print(f"Task aborted: {result.failure_reason}")

# Inspect history
print(f"Total sessions executed: {len(result.history)}")

# Get formatted summary
print(str(result))  # Prints detailed execution summary
```

## TaskStatus

Enum representing the status of a task execution.

```python
class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
```

**Values:**
- `IN_PROGRESS`: Task is still being executed
- `COMPLETED`: Task finished successfully
- `ABORTED`: Task was aborted due to unrecoverable error or impossible conditions

**Example:**
```python
from webtask import TaskStatus

result = await agent.execute("navigate to example.com")

# Compare with enum values
if result.status == TaskStatus.COMPLETED:
    print("Success!")
elif result.status == TaskStatus.ABORTED:
    print(f"Failed: {result.failure_reason}")
elif result.status == TaskStatus.IN_PROGRESS:
    print("Still running (shouldn't happen)")
```

## Complete Example

```python
from webtask import Webtask, TaskStatus
from webtask.integrations.llm import GeminiLLM

async def main():
    wt = Webtask()
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    # Execute task
    result = await agent.execute(
        "Go to google.com and search for cats",
        max_cycles=10
    )

    # Check result
    print(f"Status: {result.status}")
    print(f"Sessions executed: {len(result.history)}")

    if result.status == TaskStatus.COMPLETED:
        print("✓ Task completed successfully")
        await agent.screenshot("success.png")

    elif result.status == TaskStatus.ABORTED:
        print(f"✗ Task aborted: {result.failure_reason}")
        await agent.screenshot("failure.png")

    # Print detailed summary
    print("\n" + str(result))

    await wt.close()
```
