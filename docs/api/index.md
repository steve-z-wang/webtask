
# API Reference

Complete API documentation for webtask.


### [Agent](agent.md)
Main interface for web automation with three interaction modes.

**High-level methods:**
- `execute()` - Autonomous task execution

**Step-by-step methods:**
- `set_task()` - Set task for manual execution
- `run_step()` - Execute one step

**Low-level methods:**
- `navigate()` - Navigate to URL
- `select()` - Select element by natural language
- `wait()` / `wait_for_idle()` - Wait for conditions
- `screenshot()` - Capture screenshot

**Multi-page methods:**
- `open_page()` / `close_page()` - Manage pages
- `get_pages()` / `get_current_page()` - Access pages


### [Element](element.md)
Browser element. Returned by `agent.select()` or `page.select_one()`.

**Action methods:**
- `click()` - Click element
- `fill()` - Fill form field (instant)
- `type()` - Type text character-by-character
- `upload_file()` - Upload files

**Inspection methods:**
- `get_tag_name()` - Get tag name
- `get_attribute()` / `get_attributes()` - Get attributes
- `get_html()` - Get HTML content
- `get_parent()` / `get_children()` - Navigate DOM tree


## Data Structures

### [Data Classes](data-classes.md)
Data structures returned by webtask methods.

**TaskResult:**
- Returned from `agent.execute()`
- Contains completion status and steps

**Step:**
- Single step in task execution
- Contains proposal and execution results

**Proposal:**
- Agent's proposed actions
- Contains actions list and completion status

**ExecutionResult:**
- Result of executing an action
- Contains success status and message

**Action:**
- Single action to execute
- Contains tool name and parameters


## Next Steps

- [Getting Started](../getting-started.md) - Installation and first steps
- [Examples](../examples.md) - Complete code examples
- [Architecture](../architecture.md) - Internal design
