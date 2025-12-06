# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**webtask** is a Python library for LLM-powered web automation with autonomous agents and natural language selectors. Built on Playwright and supports Gemini/OpenAI/Bedrock multimodal LLMs.

**Four core operations:**
```python
await agent.do("click search and add first product to cart")  # Autonomous tasks
element = await agent.select("the search input")              # Element selection
data = await agent.extract("the cart total", MySchema)        # Data extraction
assert await agent.verify("cart has 1 item")                  # Verification
```

**Two modes:**
- **dom**: Element ID-based tools (click, fill, type by element ID) - default
- **pixel**: Coordinate-based tools (click_at, type_at by screen coordinates)

## Development Commands

```bash
# Setup
pip install -e ".[dev]"
playwright install chromium

# Run all PR checks (format + lint + tests)
pdm run pr

# Testing
pdm run test                    # All tests
pdm run test-unit               # Unit tests only
pdm run test-integration        # Integration tests only
pdm run test-e2e                # E2E tests (requires GEMINI_API_KEY)
pytest tests/unit/agent/test_verdict.py -v  # Single test file

# Code quality
black src/ tests/               # Format
ruff check --fix src/ tests/    # Lint with auto-fix
```

### Debugging
```bash
export WEBTASK_DEBUG=1                    # Enable debug mode
export WEBTASK_DEBUG_DIR="debug/my_test"  # Custom debug directory
```
Debug output: `debug/summary.txt` (execution summary), `*_context.txt` (LLM context), `*_img_*.png` (screenshots with bounding boxes)

## Architecture

### Core Flow
```
Webtask → Agent → TaskRunner → AgentBrowser → Playwright
           ↓
         LLM (tool calls)
```

1. **Webtask** (`webtask.py`) - Manages browser lifecycle, creates agents with isolated contexts
2. **Agent** (`agent/agent.py`) - Main interface with `do()`, `verify()`, `extract()`, `select()` methods
3. **TaskRunner** (`_internal/agent/task_runner.py`) - Executes tasks by calling LLM with available tools
4. **AgentBrowser** (`_internal/agent/agent_browser.py`) - Page management, context building, coordinate scaling

### Key Design Principles

1. **Element ID Abstraction**: LLM sees clean element IDs (`[1]`, `[2]`), browser uses XPath
2. **Multimodal Context**: LLM receives both DOM text and screenshots
3. **Public vs Internal**: `src/webtask/` is public API, `src/webtask/_internal/` is implementation details

### Module Structure

```
src/webtask/
├── webtask.py              # Webtask manager - browser lifecycle
├── agent/
│   ├── agent.py            # Agent interface (do, verify, extract, select)
│   └── result.py           # Result, Verdict data classes
├── browser/                # Abstract browser interfaces
│   ├── browser.py, context.py, page.py, element.py
├── llm/                    # LLM interfaces
│   ├── llm.py              # Abstract LLM base class
│   ├── tool.py             # Tool definition
│   └── message.py          # Message types
├── integrations/
│   ├── browser/playwright/ # Playwright implementation
│   └── llm/
│       ├── google/         # Gemini, GeminiComputerUse
│       └── bedrock/        # AWS Bedrock (Claude)
├── mcp_server/             # MCP server for Claude Desktop integration
└── _internal/              # Implementation details (not public API)
    ├── agent/
    │   ├── task_runner.py  # Executes tasks with LLM
    │   ├── agent_browser.py # Page context building
    │   ├── selector.py     # Natural language element selection
    │   └── tools/          # Tool implementations (dom/, pixel/, navigation/, etc.)
    ├── dom/                # DOM processing
    │   ├── domnode.py      # DOM tree node
    │   ├── parsers/        # CDP → DomNode
    │   └── filters/        # Remove hidden/non-semantic elements
    ├── context/            # Context building for LLM
    └── prompts/            # System prompts
```

### Tools by Mode

**Common tools (all modes):** `goto`, `go_back`, `go_forward`, `open_tab`, `switch_tab`, `key_combination`

**DOM mode:** `click`, `type`, `select`, `upload` (by element ID)

**Pixel mode:** `click_at`, `type_at`, `hover_at`, `scroll_at`, `scroll_document`, `drag_and_drop` (by coordinates)

### Adding a New Tool

1. Create tool class in `_internal/agent/tools/` (e.g., `dom.py` or `pixel.py`)
2. Inherit from `Tool`, implement `__call__` method
3. Register in `Agent._create_browser_tools()` in `agent/agent.py`
4. Update worker prompt in `_internal/prompts/worker_prompt.py` if needed

### Modifying DOM Filtering

Filters in `_internal/dom/filters/`:
- `filter_non_rendered.py` - Remove hidden elements (display:none, visibility:hidden)
- `filter_non_semantic.py` - Remove non-interactive elements (script, style, meta)

## Package Info

- **PyPI**: `pywebtask`
- **Python**: >=3.10
- **Main deps**: playwright, google-genai, pydantic, Pillow
