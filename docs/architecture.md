# Architecture

## Overview

```
┌──────────────┐
│   Webtask    │  Browser lifecycle management
└──────┬───────┘
       │ creates
       ↓
┌──────────────┐
│    Agent     │  Task execution with LLM
└──────┬───────┘
       │ uses
       ↓
┌──────────────┐
│ TaskRunner   │  Executes steps with tools
└──────┬───────┘
       │ controls
       ↓
┌──────────────┐
│AgentBrowser  │  Page management & DOM access
└──────────────┘
```

## Components

**Webtask** - Manages browser lifecycle, creates agents

**Agent** - Main interface with `do()`, `verify()`, `goto()` methods

**TaskRunner** - Executes tasks by calling LLM with available tools

**AgentBrowser** - Manages pages, builds DOM context, executes actions

## How it Works

1. User calls `agent.do("task description")`
2. TaskRunner builds context from current page (DOM + screenshot)
3. LLM decides which tools to call (navigate, click, fill, verify)
4. TaskRunner executes tools via AgentBrowser
5. Repeat until task complete or max steps reached

## Tools

Available tools for the LLM:

- `navigate` - Go to URL
- `click` - Click element
- `fill` - Fill form field
- `type` - Type text
- `upload` - Upload file
- `wait` - Wait for time
- `complete_work` - Mark task as done
- `abort_work` - Give up on task

## Stateful Mode

When `stateful=True` (default), Agent maintains conversation history across `do()` calls, allowing context to carry over between tasks.
