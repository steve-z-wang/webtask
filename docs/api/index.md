
# API Reference

Complete API documentation for webtask.


### [Agent](agent.md)
Main interface for web automation with two interaction modes.

**Autonomous mode:**
- `execute()` - Give it a task, agent figures out the steps

**Direct control mode:**
- `navigate()` - Navigate to URL
- `select()` - Select element by natural language
- `wait()` / `wait_for_idle()` - Wait for conditions
- `screenshot()` - Capture screenshot

**Multi-page management:**
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

**TaskExecution:**
- Returned from `agent.execute()`
- Contains task status, history, and subtask queue
- Fields: `status`, `history`, `subtask_queue`, `failure_reason`

**TaskStatus:**
- Enum for task status
- Values: `IN_PROGRESS`, `COMPLETED`, `ABORTED`


## Next Steps

- [Getting Started](../getting-started.md) - Installation and first steps
- [Examples](../examples.md) - Complete code examples
- [Architecture](../architecture.md) - Internal design
