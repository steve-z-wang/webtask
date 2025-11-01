# Task Context Refactoring Plan

## Problem Statement

Currently, task-scoped state (task description, step history) is mixed with agent-level state. This leads to:
- Manual history management (`clear_history=True` parameter)
- Confusing lifecycle (when do steps get cleared?)
- No systematic way to add new task-scoped features (like file resources)
- Separate `StepHistory` class that duplicates responsibility

## Solution: TaskContext

Introduce a `TaskContext` class that owns all task-scoped state. Starting a new task creates a new context, automatically cleaning up old state.

---

## Architecture Changes

### Before

```python
class Agent:
    def __init__(self, ...):
        self.current_task: Optional[str] = None
        self.step_history: StepHistory = StepHistory()
        self.proposer: Optional[Proposer] = None
        self.executer: Optional[Executer] = None

    async def execute(self, task: str, max_steps: int = 10,
                      clear_history: bool = True) -> TaskResult:
        self.set_task(task, clear_history=clear_history)
        # ...

    def set_task(self, task: str, clear_history: bool = True) -> None:
        self.current_task = task
        if clear_history:
            self.step_history.clear()
        # ...

    def clear_history(self) -> None:
        self.step_history.clear()
        self.current_task = None
        # ...
```

### After

```python
@dataclass
class TaskContext:
    """All state for a single task execution."""
    task: str
    resources: Dict[str, str] = field(default_factory=dict)
    steps: List[Step] = field(default_factory=list)
    max_steps: int = 10

    def add_step(self, step: Step) -> None:
        """Add a step to history."""
        self.steps.append(step)

    def get_steps_summary(self) -> str:
        """Format steps for LLM context (moved from StepHistory)."""
        if not self.steps:
            return "No previous steps."

        summary_lines = []
        for i, step in enumerate(self.steps, 1):
            summary_lines.append(f"Step {i}:")

            # Actions
            for action in step.proposal.actions:
                summary_lines.append(f"  - {action.tool_name}: {action.reason}")

            # Result
            if step.proposal.complete:
                summary_lines.append(f"  Result: Task complete - {step.proposal.message}")
            else:
                summary_lines.append(f"  Result: {step.proposal.message}")

        return "\n".join(summary_lines)

    def get_task_context(self) -> Block:
        """Get formatted task context for LLM."""
        return Block(f"Task:\n{self.task}")

    def get_resources_context(self) -> Optional[Block]:
        """Get formatted resources context for LLM."""
        if not self.resources:
            return None
        resources_text = "Available file resources for upload:\n"
        for name, path in self.resources.items():
            resources_text += f"- {name}: {path}\n"
        return Block(resources_text)

    def get_steps_context(self) -> Block:
        """Get formatted step history context for LLM."""
        return Block(f"Previous steps:\n{self.get_steps_summary()}")


class Agent:
    def __init__(self, ...):
        self._task_context: Optional[TaskContext] = None
        self.proposer: Optional[Proposer] = None
        self.executer: Optional[Executer] = None
        # No more current_task or step_history!

    async def execute(self, task: str, max_steps: int = 10,
                      resources: Optional[Dict[str, str]] = None) -> TaskResult:
        # Create new task context (automatic cleanup)
        self._task_context = TaskContext(
            task=task,
            resources=resources or {},
            max_steps=max_steps
        )

        self.proposer = Proposer(self.llm, self._task_context, ...)
        self.executer = Executer(...)

        for i in range(max_steps):
            step = await self.run_step()
            self._task_context.add_step(step)

            if step.proposal.complete:
                return TaskResult(
                    completed=True,
                    steps=self._task_context.steps,
                    message=step.proposal.message
                )

        return TaskResult(
            completed=False,
            steps=self._task_context.steps,
            message=f"Not completed after {max_steps} steps"
        )

    def set_task(self, task: str, max_steps: int = 10,
                 resources: Optional[Dict[str, str]] = None) -> None:
        """Set task for step-by-step execution."""
        self._task_context = TaskContext(
            task=task,
            resources=resources or {},
            max_steps=max_steps
        )

        self.proposer = Proposer(self.llm, self._task_context, ...)
        self.executer = Executer(...)

    async def run_step(self) -> Step:
        """Execute one step of current task."""
        if self._task_context is None:
            raise RuntimeError("No task set. Call set_task() first.")

        step_num = len(self._task_context.steps) + 1
        # ... propose, execute, verify ...

        self._task_context.add_step(step)
        return step

    # No more clear_history() method!
```

---

## Detailed Changes

### 1. Create TaskContext Class

**New File**: `agent/task_context.py`

```python
"""Task context - all state for a single task execution."""

from dataclasses import dataclass, field
from typing import Dict, List
from .step import Step


@dataclass
class TaskContext:
    """
    Container for all task-scoped state.

    Created when a task is set, replaced when a new task starts.
    Owns task description, resources, and execution history.
    """

    task: str
    """Task description in natural language."""

    resources: Dict[str, str] = field(default_factory=dict)
    """File resources available to this task (name -> path)."""

    steps: List[Step] = field(default_factory=list)
    """Execution history for this task."""

    max_steps: int = 10
    """Maximum steps before giving up."""

    def add_step(self, step: Step) -> None:
        """
        Add a completed step to history.

        Args:
            step: Completed step with proposal and execution results
        """
        self.steps.append(step)

    def get_steps_summary(self) -> str:
        """
        Format step history for LLM context.

        Returns:
            Human-readable summary of completed steps
        """
        if not self.steps:
            return "No previous steps."

        summary_lines = []
        for i, step in enumerate(self.steps, 1):
            summary_lines.append(f"\nStep {i}:")

            # Show proposed actions
            if step.proposal.actions:
                summary_lines.append("  Actions:")
                for action in step.proposal.actions:
                    summary_lines.append(f"    - {action.tool_name}: {action.reason}")

            # Show result
            if step.proposal.complete:
                summary_lines.append(f"  Result: ✓ Task complete - {step.proposal.message}")
            else:
                summary_lines.append(f"  Result: {step.proposal.message}")

        return "\n".join(summary_lines)

    @property
    def step_count(self) -> int:
        """Number of completed steps."""
        return len(self.steps)

    def get_task_context(self) -> Block:
        """
        Get formatted task context for LLM.

        TaskContext owns formatting of its data - Proposer just asks for formatted context.
        """
        return Block(f"Task:\n{self.task}")

    def get_resources_context(self) -> Optional[Block]:
        """
        Get formatted resources context for LLM.

        Returns None if no resources available.
        """
        if not self.resources:
            return None
        resources_text = "Available file resources for upload:\n"
        for name, path in self.resources.items():
            resources_text += f"- {name}: {path}\n"
        return Block(resources_text)

    def get_steps_context(self) -> Block:
        """Get formatted step history context for LLM."""
        return Block(f"Previous steps:\n{self.get_steps_summary()}")
```

**Design Decision**: TaskContext owns formatting of its data. Method names use `get_xxx_context()` pattern:
- **Hides implementation**: User doesn't need to know about "Block" class
- **Encapsulation**: TaskContext knows how to present itself
- **Single Responsibility**: Proposer assembles context, TaskContext formats data
- **Reusability**: Other code can easily get formatted task data
- **Maintainability**: Change formatting in one place

### 2. Update Agent Class

**File**: `agent/agent.py`

**Remove:**
```python
self.current_task: Optional[str] = None
self.step_history: StepHistory = StepHistory()
```

**Add:**
```python
from .task_context import TaskContext

self._task_context: Optional[TaskContext] = None
```

**Update `execute()` method:**
```python
async def execute(
    self,
    task: str,
    max_steps: int = 10,
    resources: Optional[Dict[str, str]] = None
) -> TaskResult:
    """
    Execute a task autonomously.

    Args:
        task: Task description in natural language
        max_steps: Maximum number of steps before giving up
        resources: Optional dict of file resources (name -> path)

    Returns:
        TaskResult with completion status, steps, and final message
    """
    # Create new task context (replaces any existing task)
    self._task_context = TaskContext(
        task=task,
        resources=resources or {},
        max_steps=max_steps
    )

    # Initialize roles
    self.proposer = Proposer(
        self.llm,
        self._task_context,
        self.tool_registry,
        self.llm_browser
    )
    self.executer = Executer(self.tool_registry, self.action_delay)

    # Execute steps
    for i in range(max_steps):
        step = await self.run_step()

        if step.proposal.complete:
            return TaskResult(
                completed=True,
                steps=self._task_context.steps,
                message=step.proposal.message,
            )

    return TaskResult(
        completed=False,
        steps=self._task_context.steps,
        message=f"Task not completed after {max_steps} steps",
    )
```

**Update `set_task()` method:**
```python
def set_task(
    self,
    task: str,
    max_steps: int = 10,
    resources: Optional[Dict[str, str]] = None
) -> None:
    """
    Set current task for step-by-step execution.

    Args:
        task: Task description in natural language
        max_steps: Maximum steps before giving up
        resources: Optional dict of file resources (name -> path)
    """
    # Create new task context
    self._task_context = TaskContext(
        task=task,
        resources=resources or {},
        max_steps=max_steps
    )

    # Initialize roles
    self.proposer = Proposer(
        self.llm,
        self._task_context,
        self.tool_registry,
        self.llm_browser
    )
    self.executer = Executer(self.tool_registry, self.action_delay)
```

**Update `run_step()` method:**
```python
async def run_step(self) -> Step:
    """
    Execute one step of the current task.

    Returns:
        Step with proposal and execution results

    Raises:
        RuntimeError: If no task is set (call set_task first)
    """
    from ..utils import wait

    if self._task_context is None or self.proposer is None:
        raise RuntimeError("No task set. Call set_task() first.")

    step_num = self._task_context.step_count + 1
    self.logger.debug(f"=== Starting Step {step_num} ===")

    # Phase 1: Propose actions and check completion
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
        success_count = sum(1 for r in exec_results if r.success)
        self.logger.debug(
            f"Execution complete: {success_count}/{len(exec_results)} successful"
        )

        # Wait for page to stabilize
        self.logger.debug(
            f"Phase 3: Waiting {self.action_delay}s for page to stabilize..."
        )
        await wait(self.action_delay)

    step = Step(proposal=proposal, executions=exec_results)
    self._task_context.add_step(step)

    self.logger.debug(f"=== Step {step_num} Complete ===\n")

    return step
```

**Remove `clear_history()` method entirely:**
```python
# DELETE THIS METHOD - no longer needed!
def clear_history(self) -> None:
    """Clear step history and task state."""
    self.step_history.clear()
    self.current_task = None
    self.proposer = None
    self.executer = None
```

### 3. Update Proposer Class

**File**: `agent/role/proposer.py`

**Change constructor:**
```python
from ..task_context import TaskContext

def __init__(
    self,
    llm: LLM,
    task_context: TaskContext,  # Changed from individual params
    tool_registry: ToolRegistry,
    llm_browser: LLMBrowser,
):
    self.llm = llm
    self.task_context = task_context
    self.tool_registry = tool_registry
    self.llm_browser = llm_browser
    # Load prompts...
```

**Update `_build_context()` method to use TaskContext context methods:**
```python
async def _build_context(self) -> Context:
    system = get_prompt("proposer_system")
    context = Context(system=system)

    # TaskContext owns formatting - we just ask for formatted context
    context.append(self.task_context.get_task_context())

    # Add resources if available
    resources_context = self.task_context.get_resources_context()
    if resources_context:
        context.append(resources_context)

    # Add step history
    context.append(self.task_context.get_steps_context())

    # Add tools and page context
    context.append(self.tool_registry.get_tools_context())
    context.append(await self.llm_browser.get_page_context())

    return context
```

**Key Design**: Proposer doesn't format task data - it asks TaskContext for formatted context. This separates concerns:
- **TaskContext**: Owns its data AND how to format it for LLM
- **Proposer**: Assembles the context from various sources
- **Consistent naming**: All components use `get_xxx_context()` pattern:
  - `TaskContext`: `get_task_context()`, `get_resources_context()`, `get_steps_context()`
  - `ToolRegistry`: `get_tools_context()`
  - `LLMBrowser`: `get_page_context()`
- **Benefits**: Hides implementation details (Block class), consistent API across components

### 4. Update StepHistory (Remove It!)

**Delete File**: `agent/step_history.py`

All functionality moved to `TaskContext.get_steps_summary()`.

### 5. Update Prompts

**File**: `prompts_data/agent/proposer.yaml`

```yaml
system: |
  You are a web automation agent. Your job is to complete tasks by interacting with web pages.

  # ... existing system prompt ...

user: |
  Task: {{ task }}

  {% if resources %}
  Available file resources for upload:
  {% for name, path in resources.items() %}
  - {{ name }}: {{ path }}
  {% endfor %}
  {% endif %}

  Current page state:
  {{ page_context }}

  {% if step_history %}
  Previous steps:
  {{ step_history }}
  {% endif %}

  Available tools:
  {{ tools }}

  # ... rest of prompt ...
```

### 6. Add File Upload Support

**New File**: `agent/tools/browser/upload.py`

```python
from typing import List
from pydantic import Field
from ...tool import Tool
from ...tool_params import ToolParams
from ....step import ExecutionResult
from ....llm_browser import LLMBrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...task_context import TaskContext


class UploadParams(ToolParams):
    """Parameters for upload tool."""

    element_id: str = Field(description="Element ID of file input")
    resource_names: List[str] = Field(description="List of resource names to upload")


class UploadTool(Tool):
    """Tool for uploading file resources to input elements."""

    def __init__(self, llm_browser: LLMBrowser, task_context: "TaskContext"):
        super().__init__(
            name="upload",
            description="Upload file resources to a file input element",
            params_class=UploadParams
        )
        self.llm_browser = llm_browser
        self.task_context = task_context

    async def execute(self, params: UploadParams) -> ExecutionResult:
        """Upload files to input element."""
        try:
            # Resolve resource names to paths
            paths = []
            for name in params.resource_names:
                path = self.task_context.resources.get(name)
                if path is None:
                    return ExecutionResult(
                        success=False,
                        error=f"Resource not found: {name}"
                    )
                paths.append(path)

            # Upload files
            await self.llm_browser.upload(
                params.element_id,
                paths if len(paths) > 1 else paths[0]
            )

            return ExecutionResult(success=True)

        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
```

**Update tool registration in `agent.py`:**
```python
def _register_tools(self) -> None:
    from .tools.browser import NavigateTool, ClickTool, FillTool, TypeTool, UploadTool

    self.tool_registry.clear()

    self.tool_registry.register(NavigateTool(self.llm_browser))
    self.tool_registry.register(ClickTool(self.llm_browser))
    self.tool_registry.register(FillTool(self.llm_browser))
    self.tool_registry.register(TypeTool(self.llm_browser))

    # Register upload tool if we have a task context with resources
    if self._task_context and self._task_context.resources:
        self.tool_registry.register(UploadTool(self.llm_browser, self._task_context))
```

**Problem**: Tools registered before task is set. **Solution**: Register tools in `set_task()` and `execute()` instead of `__init__()`.

### 7. Update LLMBrowser for Upload

**File**: `llm_browser/llm_browser.py`

```python
from typing import Union, List

async def upload(self, element_id: str, file_paths: Union[str, List[str]]) -> None:
    """
    Upload file(s) to input element.

    Args:
        element_id: Element ID from DOM
        file_paths: Single path or list of paths

    Raises:
        ValueError: If element_id not found
    """
    page = self._require_page()

    # Get element from map
    dom_node = self._element_map.get(element_id)
    if not dom_node:
        raise ValueError(f"Element ID not found: {element_id}")

    # Get XPath from original node
    original_node = dom_node.metadata.get("original_node", dom_node)
    xpath = original_node.get_xpath()

    # Upload files
    element = await page.get_element_by_xpath(xpath)
    await element.upload_file(file_paths)
```

### 8. Update Element Interface for Multiple Files

**File**: `browser/element.py`

```python
from typing import Union, List

@abstractmethod
async def upload_file(self, file_path: Union[str, List[str]]):
    """
    Upload file(s) to a file input element.

    Args:
        file_path: Single file path or list of file paths
    """
    pass
```

**File**: `integrations/browser/playwright/playwright_element.py`

```python
from typing import Union, List

async def upload_file(self, file_path: Union[str, List[str]]):
    """Upload file(s) to a file input element."""
    await self._locator.set_input_files(file_path, timeout=100)
```

---

## Migration Guide

### Breaking Changes

**Removed:**
- `execute(clear_history=True)` parameter - no longer needed
- `agent.clear_history()` method - no longer needed
- `StepHistory` class - replaced by `TaskContext`

**Changed:**
- `Proposer.__init__()` now takes `TaskContext` instead of individual params

### Code Migration

**Before:**
```python
# Execute with history cleared
result = await agent.execute("search cats", clear_history=True)

# Execute keeping history
result = await agent.execute("click first result", clear_history=False)

# Manual cleanup
agent.clear_history()
```

**After:**
```python
# Each execute() starts fresh automatically
result = await agent.execute("search cats")

# To continue same task, use step-by-step mode
agent.set_task("multi-step task")
step1 = await agent.run_step()
step2 = await agent.run_step()

# No manual cleanup needed - next task auto-replaces context
```

---

## Implementation Checklist

### Core TaskContext
- [ ] Create `agent/task_context.py` with TaskContext class
- [ ] Add `get_steps_summary()` method
- [ ] Add resource management to TaskContext

### Agent Updates
- [ ] Replace `self.current_task` and `self.step_history` with `self._task_context`
- [ ] Update `execute()` to create TaskContext and remove `clear_history` param
- [ ] Update `set_task()` to create TaskContext and add `resources` param
- [ ] Update `run_step()` to use `self._task_context`
- [ ] Remove `clear_history()` method
- [ ] Move tool registration to `set_task()` and `execute()`

### Proposer Updates
- [ ] Update `Proposer.__init__()` to accept TaskContext
- [ ] Update `propose()` to use `task_context.task`, `task_context.resources`, etc.

### File Upload Support
- [ ] Update `Element.upload_file()` signature for multiple files
- [ ] Update `PlaywrightElement.upload_file()` implementation
- [ ] Add `LLMBrowser.upload()` method
- [ ] Create `UploadTool` class
- [ ] Update prompt to include resources

### Cleanup
- [ ] Delete `agent/step_history.py`
- [ ] Update all imports

### Testing
- [ ] Update existing tests to remove `clear_history` usage
- [ ] Test task context lifecycle
- [ ] Test file upload with resources
- [ ] Test step-by-step mode with resources

### Documentation
- [ ] Update README examples
- [ ] Update CLAUDE.md architecture section
- [ ] Add file upload examples
- [ ] Document TaskContext class

---

## Benefits Summary

✅ **Cleaner API**: No more `clear_history` parameter confusion
✅ **Automatic cleanup**: New task = fresh context, no manual management
✅ **Systematic architecture**: Clear separation of agent-scoped vs task-scoped state
✅ **Extensible**: Easy to add new task-scoped features (resources, custom instructions, etc.)
✅ **Simpler code**: Remove StepHistory class, consolidate logic in TaskContext
✅ **File upload support**: Natural integration via task resources
✅ **Better encapsulation**: Task owns its steps, resources, and configuration

---

## Timeline Estimate

- **TaskContext creation + Agent updates**: 2-3 hours
- **File upload implementation**: 2 hours
- **Testing + fixes**: 2 hours
- **Documentation updates**: 1 hour

**Total**: ~7-8 hours of focused work
