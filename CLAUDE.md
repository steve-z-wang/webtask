# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**webtask** is a Python library for LLM-powered web automation with autonomous agents and natural language selectors. Built on Playwright for browser automation and supports OpenAI/Gemini multimodal LLMs with screenshot capabilities.

Three interaction modes:
- **High-level autonomous**: `agent.execute(task)` - Agent autonomously plans and executes steps with visual + text context
- **Step-by-step**: `agent.set_task()` + `agent.execute_step()` loop - Manual control of agent loop for debugging
- **Low-level imperative**: `agent.navigate()`, `agent.select()`, `agent.wait()` - Direct control with natural language selectors

**Multimodal by default**: Agent sees both DOM text (element IDs) and screenshots with bounding boxes for better accuracy.

## Development Commands

### Setup
```bash
# Install in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pdm run test

# Run with coverage
pdm run test-cov

# Run unit tests only
pdm run test-unit

# Run integration tests only
pdm run test-integration

# Run e2e tests in live mode (requires browser and LLM API)
pdm run test-e2e

# Run e2e tests in record mode (records browser/LLM interactions)
pdm run test-e2e-record

# Run e2e tests in replay mode (fast, deterministic, offline)
pdm run test-e2e-replay

# Run specific test file
pytest tests/test_dom.py -v

# Run tests with specific marker
pytest -m unit -v
pytest -m integration -v
pytest -m e2e -v
```

### Code Quality
```bash
# Format code with black
black src/

# Lint with ruff
ruff check src/

# Auto-fix linting issues
ruff check --fix src/
```

### Package Building
```bash
# Build package
python -m build

# Upload to PyPI (requires credentials)
python -m twine upload dist/*
```

### Debugging
```bash
# Enable debug mode (saves screenshots, context, and execution summary)
export WEBTASK_DEBUG=1

# Optional: Set custom debug directory (default: "debug")
export WEBTASK_DEBUG_DIR="debug/my_test"

# Run your script/test with debug enabled
python my_script.py

# Debug output includes:
# - debug/summary.txt - Complete task execution summary with all sessions and subtasks
# - debug/*_context.txt - LLM context (text) for each iteration
# - debug/*_img_*.png - Screenshots with bounding boxes for each iteration
```

The `summary.txt` file contains the complete `TaskExecution` output including:
- Task description and status (completed/aborted/in_progress)
- Subtask queue state
- Full execution history with all manager sessions and subtask executions
- Tool calls and their results

## Architecture

### Core Design Principles

1. **Element ID Abstraction**: LLM sees clean element IDs (`button-0`, `input-1`), browser uses XPath
2. **Multimodal Context**: LLM receives both text (DOM tree) and visual (screenshot with bounding boxes) context
3. **XPath from Original DOM**: Element XPaths computed from unfiltered DOM tree to match actual browser state
4. **Separation of Concerns**: DOM layer is pure data structures, doesn't know about LLMs or browsers
5. **Role-Based Architecture**: Separate roles (Verifier, Proposer, Planner) with distinct tool registries, Executer runs actions
6. **Composable Context Building**: Block system supports text + images for multimodal LLM APIs
7. **Lazy Initialization**: Browser launches only when first agent is created

### Module Structure

```
src/webtask/
├── webtask.py              # Webtask manager - browser lifecycle, lazy init
├── agent/                  # Agent orchestration
│   ├── agent.py           # Main agent interface (3 modes: execute/step/imperative)
│   ├── task_executor.py   # TaskExecutor - executes tasks with roles
│   ├── step.py            # ExecutionResult, Step, TaskResult
│   ├── task.py            # Task - manages task state & history
│   ├── tool.py            # Base Tool class + ToolRegistry
│   ├── throttler.py       # Throttler - rate limiting
│   ├── roles/             # Agent roles with specialized behaviors
│   │   ├── base_role.py   # BaseRole - abstract base with propose_actions() and execute()
│   │   ├── proposer.py    # ProposerRole - proposes browser actions
│   │   └── verifier.py    # VerifierRole - checks task completion
│   ├── schemas/           # Pydantic models for LLM responses
│   │   ├── params.py      # ToolParams (ClickParams, FillParams, etc.)
│   │   ├── actions.py     # Action union (ClickAction, FillAction, etc.)
│   │   ├── mode.py        # Proposal, Mode enum
│   │   └── selector.py    # SelectorResponse
│   ├── tools/browser/     # Concrete browser action tools
│   │   ├── navigate.py
│   │   ├── click.py
│   │   ├── fill.py        # Fill form fields by element_id
│   │   ├── type.py        # Type into elements by element_id
│   │   └── upload.py      # Upload files by element_id
│   └── tools/control/     # Control tools
│       └── mark_complete.py # Signal task completion
├── llm_browser/           # Bridge between LLM text and browser operations
│   ├── llm_browser.py    # Element ID mapping, context building, action execution
│   ├── dom_context_builder.py  # Builds text DOM context
│   ├── bounding_box_renderer.py # Renders screenshots with bounding boxes
│   ├── dom_filter_config.py  # DOM filtering configuration
│   └── selector.py       # Natural language element selection
├── browser/               # Abstract browser interfaces
│   ├── browser.py        # Browser management
│   ├── session.py        # Session/context management
│   ├── page.py           # Page operations
│   ├── element.py        # Element actions
│   └── cookies.py        # Cookie management
├── dom/                   # Pure DOM data structures
│   ├── domnode.py        # DOM tree node with traversal and xpath
│   ├── snapshot.py       # DomSnapshot - root + metadata
│   ├── selector.py       # XPath class for browser element selection
│   ├── parsers/          # Convert to DomNode (CDP, HTML)
│   ├── filters/          # Clean DOM for LLM (visibility, semantic)
│   ├── serializers/      # Convert DomNode to markdown
│   └── utils/            # add_node_reference.py - preserves original nodes
├── llm/                   # LLM interfaces
│   ├── llm.py            # Abstract LLM base class with logging
│   ├── context.py        # Context (system + user blocks) and Block (text + image)
│   └── tokenizer.py      # Token counting
├── media/                 # Media handling
│   └── image.py          # Image class (base64, data URL, save to file)
├── integrations/          # Concrete implementations
│   ├── browser/playwright/ # Playwright implementation
│   │   ├── playwright_browser.py
│   │   ├── playwright_session.py
│   │   ├── playwright_page.py  # XPath-based element selection
│   │   └── playwright_element.py
│   └── llm/
│       ├── openai/       # OpenAI GPT models (multimodal support)
│       └── google/       # Google Gemini models (multimodal support)
├── prompts/              # LLM prompts loaded from prompts_data/
│   └── prompt_library.py
├── prompts_data/         # YAML files with prompts
│   ├── agent/           # proposer.yaml, verifier.yaml
│   └── selector/        # natural_selector.yaml
└── utils/                # Shared utilities
    ├── json_parser.py    # parse_json() with markdown fence handling
    ├── url.py           # normalize_url()
    └── wait.py          # wait() helper
```

### Key Components

**Webtask Manager** (`webtask.py`)
- Top-level orchestrator managing browser lifecycle
- Lazy browser initialization (launches on first `create_agent()` call)
- Creates agents with isolated sessions

**Agent** (`agent/agent.py`)
- Main user interface with three modes:
  - High-level: `execute(task)` - autonomous loop
  - Step-by-step: `set_task()` + `execute_step()` - manual control
  - Low-level: `navigate()`, `select()`, `wait()` - imperative control
- **Requires Session** (not optional) - proper abstraction for browser management
- Multi-page support: `open_page()`, `close_page()`, `set_page()`, `get_pages()`
- `select()` method uses `NaturalSelector(self.llm, self.llm_browser)` for natural language element selection
- Creates `LLMBrowser(session, use_screenshot)` - note: NO llm parameter!

**LLMBrowser** (`llm_browser/llm_browser.py`)
- Pure page management and context building (**NO LLM dependency**)
- Manages multiple pages/tabs
- Delegates to `WebContextBuilder` for context building
- Maintains `element_map`: element_id → DomNode → XPath
- **Critical**: Uses `original_node` metadata to compute XPath from unfiltered DOM tree
- Executes actions by converting element IDs to XPath selectors (navigate, click, keyboard_type)
- Does NOT have `select()` method - that's an Agent feature

**WebContextBuilder** (`llm_browser/web_context_builder.py`)
- Static method: `build_context(page, dom_context_config) -> (str, Dict[str, DomNode])`
- Pure function - no state, no side effects
- Applies filters, assigns element IDs, serializes to markdown
- Returns string (not Block) for framework-agnostic reusability

**Step System** (`agent/step.py`)
- Tracks full cycles instead of just actions
- **Step** = Proposal + ExecutionResult(s)
- **Task** (`agent/task.py`) manages task state and stores step history for agent reasoning
- **TaskResult** returned from `execute()` with completion status
- Step completion checked by presence of mark_complete action

**TaskExecutor** (`agent/task_executor.py`)
- Executes a task with roles
- Does NOT own Task (Agent owns it) - receives Task as parameter
- Creates throttler and all roles (VerifierRole, ProposerRole)
- Runs full cycle: select role → propose_actions() → execute() → create Step → record history
- Tracks current mode and handles transitions
- Agent delegates to `task_executor.run_step()`

**Agent Roles** (`agent/roles/`)
- **BaseRole** (`roles/base_role.py`): Abstract base class with two methods:
  - `propose_actions()` - thinking phase, calls LLM to decide what to do
  - `execute(actions)` - doing phase, executes actions using role's tool registry
- **ProposerRole** (`roles/proposer.py`): Proposes browser actions (navigate, click, fill, type, upload)
- **VerifierRole** (`roles/verifier.py`): Checks if task is complete (uses mark_complete tool)

**Pydantic Schemas** (`agent/schemas/`)
- Centralized location for all LLM response models
- **params.py**: ToolParams base class + all parameter classes (ClickParams, FillParams, MarkCompleteParams, etc.)
- **actions.py**: Action union (ClickAction, FillAction, MarkCompleteAction, etc.) with nested typed parameters
- **mode.py**: Proposal (unified schema for all roles), Mode enum (PROPOSE, VERIFY, PLAN)
- **selector.py**: SelectorResponse for natural language selection
- LLM returns JSON strings, app deserializes with `Proposal.model_validate(response_dict)`
- Type-safe with automatic Pydantic validation

**Block System** (`llm/context.py`)
- Composable context building
- **Block**: Text container with nested blocks
- **Context**: System prompt + list of user Blocks
- Components provide `to_context_block()` method

**Tools** (`agent/tool.py`, `agent/tools/`)
- Define actions agent can perform (navigate, click, type, fill, upload)
- Tool has name, description, Pydantic parameters (from `agent/schemas/params.py`)
- ToolRegistry (in `agent/tool.py`) provides schemas to LLM
- Tool implementations hold reference to LLMBrowser for execution

**DOM Processing** (`dom/`)
- Pure data structures representing DOM tree
- **Parsers**: Convert CDP/HTML → DomNode tree
- **Filters**: Remove hidden/non-interactive elements
- **Serializers**: Convert DomNode → markdown for LLM
- **add_node_reference**: Preserves original node references through filtering (critical for XPath computation)

**Prompts** (`prompts/`, `prompts_data/`)
- All LLM prompts stored as YAML in `prompts_data/`
- Accessed via `get_prompt()` from `prompts/prompt_library.py`
- Prompts loaded once and cached
- Key prompts: `proposer_system`, `verifier_system`, `selector_system`

### Important Implementation Details

**XPath from Original DOM**
- Filtered DOM shown to LLM, but XPath must reference original unfiltered DOM
- `add_node_reference.py` preserves `original_node` metadata during filtering
- LLMBrowser computes XPath from original node to match browser's actual DOM

**Element ID Mapping Flow**
1. Get DOM snapshot from browser (CDP)
2. Apply visibility filters (hidden elements)
3. Apply semantic filters (non-interactive elements)
4. Assign element IDs (`button-0`, `input-1`)
5. Serialize to markdown with IDs
6. LLM proposes action with element ID
7. LLMBrowser converts element ID → DomNode → XPath (from original node)
8. Browser executes XPath selection

**Task Execution Loop**
1. Agent creates Task (owns task state and history)
2. Agent creates TaskExecutor (receives Task, executes it)
3. TaskExecutor selects role based on current mode (PROPOSE or VERIFY)
   - **ProposerRole**: for proposing browser actions to advance task
   - **VerifierRole**: for checking if task is complete
4. Role.propose_actions() → calls LLM, returns Proposal (thinking phase)
5. Role.execute(proposal.actions) → executes actions using role's tool registry (doing phase)
6. TaskExecutor creates Step from proposal + execution results
7. TaskExecutor records step in task history
8. TaskExecutor transitions to next mode based on proposal.next_mode
9. Repeat until mark_complete action or max steps reached

**Type vs Fill**
- `type`: Uses click + keyboard typing (more realistic, slower)
- `fill`: Direct element value setting (faster, less realistic)
- Recent change moved from fill-based to type-based workflow

## Working with This Codebase

### Common Patterns

**Creating an agent**
```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

wt = Webtask(headless=False)
llm = GeminiLLM.create(model="gemini-2.5-flash")
agent = await wt.create_agent(llm=llm, action_delay=1.0)
```

**Adding a new browser action tool**
1. Create file in `agent/tools/browser/`
2. Define Pydantic params class inheriting from `ToolParams`
3. Define Tool class with `execute()` method
4. Register in `ToolRegistry`
5. Update prompts if needed

**Modifying DOM filtering**
- Visibility filters: `dom/filters/visibility/`
- Semantic filters: `dom/filters/semantic/`
- **Must** preserve original node references for XPath computation

**Changing prompts**
- Edit YAML files in `prompts_data/`
- Test thoroughly - prompt changes significantly affect behavior
- Restart application to reload (prompts are cached)

### Testing Status

**Currently**: No automated tests (see `docs/todo.md` for testing plan)

**Manual testing completed**:
- High-level autonomous mode (`agent.execute()`)
- Step-by-step execution mode
- Low-level imperative mode
- Both OpenAI and Gemini LLM providers
- Multi-step workflows (e.g., e-commerce cart)
- Error handling

**Testing TODO**: Unit tests, integration tests, end-to-end tests, benchmark evaluation (Mind2Web, WebArena)

### Package Info

- **Published as**: `pywebtask` on PyPI
- **Current version**: 0.4.1
- **Python support**: >=3.10
- **Main dependencies**: playwright, openai, google-generativeai, pydantic, lxml, tiktoken

### Examples

See `examples/` directory:
- `tool_website_demo.ipynb` - Jupyter notebook demonstration
- `google_search.ipynb` - Google search example
- `existing_browser_integration.py` - Connect to existing browser

## Notes

- Browser launches lazily on first `create_agent()` call
- Agent sessions are isolated (separate cookies, storage)
- Screenshots saved with `agent.screenshot(path)`
- Action delay configurable per agent (default 1.0s)
- Full debug logging available (no truncation of prompts/responses)
- DOM filtering is configurable via `DomFilterConfig`
