# MCP Server

The webtask MCP (Model Context Protocol) server allows you to integrate web automation capabilities into Claude Desktop and other MCP-compatible clients.

## Installation

### Prerequisites

You need Chrome or Chromium installed on your system. The MCP server connects to your existing Chrome installation.

- **macOS**: Chrome is usually at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Windows**: Chrome is usually at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **Linux**: Chrome is usually at `/usr/bin/google-chrome`

### Install webtask

Install webtask with MCP support:

```bash
pip install pywebtask[mcp]
```

**Note**: This installs the Python packages only. It does NOT install Chrome - you must have Chrome already installed on your system.

## Configuration

### Claude Desktop Setup

Add the MCP server to your Claude Desktop configuration file:

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

### Initial Setup

When you first use the MCP server, you'll need to run the onboarding process:

1. **Call the `onboard` tool** in Claude Desktop
   - Optionally specify Chrome path, debug port, and data directory
   - The tool will auto-detect Chrome if not provided

2. **Edit the configuration file** at `~/.config/webtask/config.json`:

```json
{
  "llm": {
    "provider": "gemini",
    "gemini": {
      "api_key": "YOUR_GEMINI_API_KEY_HERE"
    },
    "bedrock": {
      "region": "us-east-1",
      "bearer_token": ""
    }
  },
  "browser": {
    "chrome_path": "/path/to/chrome",
    "debug_port": 9222,
    "data_dir": "~/.config/webtask/browser-data"
  }
}
```

3. **Set your LLM provider**:
   - For **Gemini**: Set `llm.provider` to `"gemini"` and add your API key to `llm.gemini.api_key`
   - For **AWS Bedrock**: Set `llm.provider` to `"bedrock"` and configure `llm.bedrock` settings

4. **Restart Claude Desktop** to apply the configuration

## Available Tools

The MCP server provides four tools:

### onboard

Set up webtask configuration (Chrome path, debug port, data directory). This tool only appears if configuration doesn't exist.

**Parameters**:
- `chrome_path` (optional): Path to Chrome executable (auto-detected if not provided)
- `debug_port` (optional): Chrome debug port (default: 9222)
- `data_dir` (optional): Directory for browser data (default: `~/.config/webtask/browser-data`)

### start_web_agent

Start a new browser agent session. Returns a session ID to use with other tools.

**Returns**: Session ID string

**Example**:
```
Use the start_web_agent tool to create a new session
```

### do_web_task

Execute a web automation task in an existing agent session.

**Parameters**:
- `session_id` (required): Session ID from start_web_agent
- `task` (required): Task description in natural language
- `max_steps` (optional): Maximum steps to execute (default: 20)

**Example**:
```
Use do_web_task with session_id "abc-123" and task "Search for Python tutorials on Google"
```

### close_web_agent

Close an agent session and clean up resources. Chrome browser remains running.

**Parameters**:
- `session_id` (required): Session ID to close

**Example**:
```
Use close_web_agent with session_id "abc-123"
```

## Usage Workflow

### Basic Example

1. **Start an agent**:
   ```
   Start a web agent session
   ```

2. **Execute tasks**:
   ```
   Navigate to Google and search for "web automation"
   ```

3. **Close the session**:
   ```
   Close the web agent session
   ```

### Multi-Session Example

You can run multiple agent sessions concurrently:

```
Start three web agent sessions for parallel tasks
```

Each session gets its own browser context (isolated cookies, storage) but shares the same Chrome instance.

## Persistent Browser Sessions

The MCP server uses Chrome's `user-data-dir` to maintain persistent browser sessions across restarts:

- **Cookies and logins persist** - You can log into websites once and stay logged in
- **Browser state preserved** - Settings, extensions, and browsing history are maintained
- **Chrome runs continuously** - Closing agent sessions doesn't close Chrome

To fully reset browser state, delete the browser data directory:

```bash
rm -rf ~/.config/webtask/browser-data
```

## Debugging

### Logs

All webtask logs are saved to `~/.config/webtask/mcp_server.log`:

```bash
# Monitor logs in real-time
tail -f ~/.config/webtask/mcp_server.log
```

### MCP Inspector

For development and debugging, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python -m webtask.mcp_server
```

This provides a web UI at `http://localhost:5173` to test MCP tools interactively.

## Supported LLM Providers

### Google Gemini

1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set in config:
   ```json
   {
     "llm": {
       "provider": "gemini",
       "gemini": {
         "api_key": "your-api-key-here"
       }
     }
   }
   ```

### AWS Bedrock

**Option 1: Bearer Token**
```json
{
  "llm": {
    "provider": "bedrock",
    "bedrock": {
      "region": "us-east-1",
      "bearer_token": "your-bearer-token-here"
    }
  }
}
```

**Option 2: AWS Credentials**
```json
{
  "llm": {
    "provider": "bedrock",
    "bedrock": {
      "region": "us-east-1",
      "bearer_token": ""
    }
  }
}
```

With an empty bearer token, webtask will use your AWS credentials from environment variables or `~/.aws/credentials`.

## Troubleshooting

### "Configuration not found" error

Run the `onboard` tool first to create the configuration file.

### "Gemini API key not configured" error

Edit `~/.config/webtask/config.json` and set a valid API key in `llm.gemini.api_key`.

### "Chrome startup timeout" error

Check that:
- Chrome path is correct in config
- Port 9222 is not blocked by firewall
- No other process is using the debug port

### "Invalid session ID" error

The session may have been closed or expired. Start a new session with `start_web_agent`.

### Tasks not completing

Some tasks may require more steps than the default limit. Increase `max_steps` when calling `do_web_task`:

```
Execute the task with max_steps set to 50
```

## Security Considerations

- **API keys are stored in plaintext** in `~/.config/webtask/config.json` - ensure proper file permissions
- **Browser sessions persist** - be cautious when using on shared machines
- **Chrome runs with remote debugging enabled** - only use on trusted networks
- **MCP server has full browser control** - only connect to trusted MCP clients

## Next Steps

- Explore [Examples](examples.md) for common automation patterns
- Learn about the [Architecture](architecture.md) to understand how webtask works
- Check the [API Reference](api/index.md) for programmatic usage
