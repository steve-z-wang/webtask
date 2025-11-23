# Architecture

## Overview

```
┌──────────────┐
│   Webtask    │  Browser lifecycle management
└──────┬───────┘
       │ creates
       ↓
┌──────────────┐
│    Agent     │  Task execution with LLM (text/visual/full mode)
└──────┬───────┘
       │ uses
       ↓
┌──────────────┐
│ TaskRunner   │  Executes steps with tools
└──────┬───────┘
       │ controls
       ↓
┌──────────────┐
│AgentBrowser  │  Page management, context building, coordinate scaling
└──────────────┘
```

## Components

**Webtask** - Manages browser lifecycle, creates agents

**Agent** - Main interface with `do()`, `verify()`, `extract()` methods. Supports three modes.

**TaskRunner** - Executes tasks by calling LLM with available tools

**AgentBrowser** - Manages pages, builds context (DOM and/or screenshots), scales coordinates

## Three Modes

- **text** - DOM-based tools (click, fill, type by element ID)
- **visual** - Pixel-based tools (click_at, type_text_at by coordinates)
- **full** - Both DOM and pixel tools

## How it Works

1. User calls `agent.do("task description")`
2. TaskRunner builds context based on mode (DOM, screenshot, or both)
3. LLM decides which tools to call
4. TaskRunner executes tools via AgentBrowser
5. Repeat until task complete or max steps reached

## Tools

**Common tools (all modes):**
- `goto` - Navigate to URL
- `wait` - Wait for time
- `go_back` / `go_forward` - Browser history
- `complete_work` / `abort_work` - Task completion

**Text mode tools:**
- `click` - Click element by ID
- `fill` - Fill form field by ID
- `type` - Type into element by ID

**Visual mode tools:**
- `click_at` - Click at coordinates
- `type_text_at` - Type at coordinates
- `hover_at` - Hover at coordinates
- `scroll_at` - Scroll at coordinates
- `drag_and_drop` - Drag between coordinates

## Stateful Mode

When `stateful=True` (default), Agent maintains conversation history across `do()` calls, allowing context to carry over between tasks.
