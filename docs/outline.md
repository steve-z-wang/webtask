# Architecture Outline

## Core Modules

```
webtask/
├── agent/                  # Main agent interface and orchestration
│   ├── agent.py           # Agent class - high-level execute() + low-level select()/navigate()
│   ├── step.py            # Action, ExecutionResult, VerificationResult, Step, TaskResult
│   ├── step_history.py    # Tracks completed agent cycles
│   ├── role/              # Agent roles for propose-execute-verify loop
│   │   ├── proposer.py    # Proposes next action using LLM
│   │   ├── executer.py    # Executes actions and returns results
│   │   └── verifier.py    # Verifies task completion
│   ├── tool/              # Tool infrastructure
│   │   ├── tool.py        # Base Tool class with validation and execution
│   │   ├── tool_params.py # Base class for tool parameters (Pydantic)
│   │   └── tool_registry.py # Manages available tools
│   └── tools/             # Concrete tool implementations
│       └── browser/       # Browser action tools
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
│   ├── session.py        # Session management (create pages)
│   ├── page.py           # Page operations (navigate, select, get_snapshot)
│   └── element.py        # Element actions (click, fill, upload_file)
│
├── dom/                   # Pure data structures for DOM representation
│   ├── domnode.py        # DOM tree node with traversal and xpath
│   ├── snapshot.py       # DomSnapshot - root + metadata
│   ├── parsers/          # Convert to DomNode
│   │   ├── cdp.py       # Chrome DevTools Protocol
│   │   └── html.py      # HTML string
│   ├── filters/          # Clean DOM for LLM context
│   │   ├── visibility/  # Remove hidden elements
│   │   └── semantic/    # Remove non-interactive elements
│   ├── serializers/      # Convert DomNode to text
│   │   └── markdown.py  # Markdown format for LLM
│   └── utils/
│       └── add_node_reference.py # Add parent references for traversal
│
├── llm/                   # LLM interfaces and context building
│   ├── llm.py            # Abstract LLM base class
│   ├── context.py        # Context (system + user blocks) and Block (composable text)
│   └── tokenizer.py      # Token counting
│
├── integration/           # Concrete implementations
│   ├── browser/
│   │   └── playwright/   # Playwright browser implementation
│   └── llm/
│       ├── openai.py     # OpenAI GPT integration
│       └── gemini.py     # Google Gemini integration
│
└── utils/                 # Shared utilities
    └── json_parser.py    # parse_json() helper

```

## Key Components

### Agent
**Entry point** - Provides dual interface:
- **High-level**: `execute(task)` - Autonomous agent loop (propose → execute → verify)
- **Low-level**: `navigate()`, `select()` - Direct control with natural language

### LLMBrowser
**Bridge between LLM and browser** - Handles element ID abstraction:
- Assigns element IDs (`button-0`, `input-1`) to filtered DOM
- Maintains element_map (element_id → DomNode → xpath)
- Provides context with element IDs for LLM
- Executes actions by converting element IDs to selectors

### Step System
**Full cycle tracking** instead of just actions:
- **Step** = Action + ExecutionResult + VerificationResult
- **StepHistory** stores completed cycles for agent reasoning
- **TaskResult** returned from execute() with completion status

### Roles
**Three specialized agents** working together:
- **Proposer**: Analyzes task + history + page → proposes Action
- **Executer**: Executes Action → returns ExecutionResult
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
2. **Element ID Abstraction**: LLM sees `button-0`, browser sees CSS/XPath
3. **Pure Data Structures**: Action, Step, DomNode are data-only
4. **Type Safety**: Pydantic for parameter validation and schema generation
5. **Composability**: Block system for flexible context building
