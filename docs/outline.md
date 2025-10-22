# Architecture Outline

## Core Modules

```
webtask/
├── webtask.py             # Webtask manager - browser lifecycle, agent creation
│
├── agent/                 # Main agent interface and orchestration
│   ├── agent.py          # Agent class - high-level execute() + low-level select()/navigate()/wait()
│   ├── step.py           # Action, ExecutionResult, VerificationResult, Step, TaskResult
│   ├── step_history.py   # Tracks completed agent cycles
│   ├── role/             # Agent roles for propose-execute-verify loop
│   │   ├── proposer.py   # Proposes next action(s) using LLM
│   │   ├── executer.py   # Executes actions and returns results
│   │   └── verifier.py   # Verifies task completion
│   ├── tool/             # Tool infrastructure
│   │   ├── tool.py       # Base Tool class with validation and execution
│   │   ├── tool_params.py # Base class for tool parameters (Pydantic)
│   │   └── tool_registry.py # Manages available tools
│   └── tools/            # Concrete tool implementations
│       └── browser/      # Browser action tools
│           ├── navigate.py
│           ├── click.py
│           └── fill.py
│
├── llm_browser/           # Bridges LLM text interface with browser operations
│   ├── llm_browser.py    # Element ID mapping, context building, action execution
│   └── selector.py       # Natural language element selection using LLM
│
├── browser/               # Abstract browser interfaces
│   ├── browser.py        # Browser management (create sessions)
│   ├── session.py        # Session management (create pages/tabs)
│   ├── page.py           # Page operations (navigate, select, wait_for_idle, get_snapshot)
│   ├── element.py        # Element actions (click, fill, upload_file)
│   └── cookies.py        # Cookie management
│
├── dom/                   # Pure data structures for DOM representation
│   ├── domnode.py        # DOM tree node with traversal and xpath
│   ├── snapshot.py       # DomSnapshot - root + metadata
│   ├── selector.py       # XPath class for browser element selection
│   ├── parsers/          # Convert to DomNode
│   │   ├── cdp.py       # Chrome DevTools Protocol
│   │   └── html.py      # HTML string
│   ├── filters/          # Clean DOM for LLM context
│   │   ├── visibility/  # Remove hidden elements
│   │   └── semantic/    # Remove non-interactive elements
│   ├── serializers/      # Convert DomNode to text
│   │   └── markdown.py  # Markdown format for LLM
│   └── utils/
│       └── add_node_reference.py # Preserve original node references through filtering
│
├── llm/                   # LLM interfaces and context building
│   ├── llm.py            # Abstract LLM base class with logging
│   ├── context.py        # Context (system + user blocks) and Block (composable text)
│   └── tokenizer.py      # Token counting
│
├── integrations/          # Concrete implementations (note: plural)
│   ├── browser/
│   │   └── playwright/   # Playwright browser implementation
│   │       ├── playwright_browser.py  # Browser lifecycle
│   │       ├── playwright_session.py  # Session/context management
│   │       ├── playwright_page.py     # Page operations with XPath support
│   │       └── playwright_element.py  # Element interactions
│   └── llm/
│       ├── openai/       # OpenAI integration
│       │   ├── openai.py          # GPT implementation with logging
│       │   └── tiktoken_tokenizer.py # Token counting
│       └── google/       # Google integration
│           ├── gemini.py          # Gemini implementation with logging
│           └── gemini_tokenizer.py # Token counting
│
└── utils/                 # Shared utilities
    ├── json_parser.py    # parse_json() with markdown fence handling
    └── url.py            # normalize_url() helper

```

## Key Components

### Webtask Manager
**Top-level orchestrator** - Manages browser lifecycle:
- Lazy browser initialization (launches on first agent creation)
- Creates agents with isolated sessions
- Supports multiple concurrent agents
- Handles cleanup of all resources

### Agent
**Main user interface** - Provides dual interaction modes:
- **High-level**: `execute(task)` - Autonomous agent loop (propose → execute → verify)
- **Low-level**: `navigate()`, `select()`, `wait()`, `wait_for_idle()` - Direct control with natural language
- **Multi-tab support**: `new_tab()`, `switch_tab()`, `close_tab()` - Manage multiple pages

### LLMBrowser
**Bridge between LLM and browser** - Handles element ID abstraction:
- Assigns element IDs (`button-0`, `input-1`) to filtered DOM
- Maintains element_map (element_id → DomNode → XPath)
- **XPath from original DOM**: Uses `original_node` metadata to compute XPath from unfiltered tree
- Provides context with element IDs for LLM
- Executes actions by converting element IDs to XPath selectors

### Step System
**Full cycle tracking** instead of just actions:
- **Step** = Action + ExecutionResult + VerificationResult
- **StepHistory** stores completed cycles for agent reasoning
- **TaskResult** returned from execute() with completion status

### Roles
**Three specialized agents** working together:
- **Proposer**: Analyzes task + history + page → proposes Action(s)
- **Executer**: Executes Action(s) → returns ExecutionResult(s)
- **Verifier**: Checks if task complete → returns VerificationResult

### Block System
**Composable context building**:
- **Block**: Text container that can hold nested blocks
- **Context**: System prompt + list of Blocks for user prompt
- Each component provides `to_context_block()` method

### Tools
**Actions the agent can perform**:
- Tool defines name, description, parameters (Pydantic schema)
- ToolRegistry manages tools and provides schemas to LLM
- Implementations hold reference to LLMBrowser for execution

## Design Principles

1. **Separation of Concerns**: DOM layer is pure data, doesn't know about LLMs
2. **Element ID Abstraction**: LLM sees `button-0`, browser sees XPath
3. **XPath from Unfiltered DOM**: Compute XPath using original node references to match actual browser DOM
4. **Pure Data Structures**: Action, Step, DomNode are data-only
5. **Type Safety**: Pydantic for parameter validation and schema generation
6. **Composability**: Block system for flexible context building
7. **Logging**: Comprehensive logging at all layers (LLM calls, token usage, browser actions)
8. **Lazy Initialization**: Browser launches only when needed, reducing startup overhead
