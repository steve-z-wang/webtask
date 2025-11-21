# MCP Server

**Work in progress** - MCP server integration is currently under development.

The webtask MCP (Model Context Protocol) server allows you to integrate web automation capabilities into Claude Desktop and other MCP-compatible clients.

## Installation

```bash
pip install pywebtask[mcp]
```

Requires Chrome or Chromium installed on your system.

## Configuration

Add to Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "webtask": {
      "command": "python",
      "args": ["-m", "webtask.mcp_server"]
    }
  }
}
```

## Setup

1. Call the `onboard` tool in Claude Desktop
2. Edit `~/.config/webtask/config.json` and add your Gemini API key
3. Restart Claude Desktop

## Available Tools

- `start_web_agent` - Start a new browser session
- `do_web_task` - Execute a task with natural language
- `close_web_agent` - Close a session

## Basic Usage

```
Start a web agent session
Navigate to Google and search for "web automation"
Close the web agent session
```
