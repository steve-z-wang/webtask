# File Upload Support - Design Document

## Overview

File upload support is important for web automation tasks like:
- Profile pictures
- Documents (PDFs, CSVs)
- Product images for listings (e.g., Poshmark)
- Attachments and forms

This document outlines the design for adding file upload capabilities to webtask agents.

---

## Key Considerations

1. **How file uploads work**: Typically through `<input type="file">` elements - Playwright supports this via `set_input_files()`
2. **Resource types**: Images, PDFs, CSVs, videos - basically any file
3. **LLM interaction**: How does the LLM refer to files? Exact paths aren't natural language friendly
4. **Scope**: Should resources be agent-scoped or task-scoped?

---

## Proposed Design

### Resource Registry Approach

A **resource registry** where users provide resources with descriptive names that the LLM can reference naturally:

```python
# User provides resources with descriptive names
agent.add_resource("listing_image_1", "/path/to/product1.jpg")
agent.add_resource("listing_image_2", "/path/to/product2.jpg")
agent.add_resource("receipt", "/path/to/receipt.pdf")

# Or set multiple at once
agent.set_resources({
    "listing_image_1": "/path/to/product1.jpg",
    "listing_image_2": "/path/to/product2.jpg",
})

# LLM refers to resources by name in task
result = await agent.execute("upload listing_image_1 and listing_image_2 to the product photos")
```

### Why This Approach?

✅ **Natural for LLM**: Refers to "listing_image_1" instead of "/home/user/photos/IMG_1234.jpg"
✅ **Decouples task from filesystem**: User manages paths, LLM manages logic
✅ **Flexible**: Support single or multiple files
✅ **Simple state**: Just a dict mapping names to paths

---

## Implementation Plan

### 1. Agent Resource Management

**File**: `agent/agent.py`

```python
class Agent:
    def __init__(self, ...):
        self.resources: Dict[str, str] = {}  # name -> file path

    def add_resource(self, name: str, path: str) -> None:
        """
        Add a file resource by descriptive name.

        Args:
            name: Descriptive name for the resource (e.g., "listing_image_1")
            path: Absolute path to the file
        """

    def set_resources(self, resources: Dict[str, str]) -> None:
        """
        Set all resources at once (replaces existing).

        Args:
            resources: Dictionary mapping names to file paths
        """

    def clear_resources(self) -> None:
        """Clear all resources."""

    def get_resource(self, name: str) -> Optional[str]:
        """
        Get resource path by name.

        Args:
            name: Resource name

        Returns:
            File path or None if not found
        """
```

### 2. Upload Tool

**File**: `agent/tools/browser/upload.py`

```python
class UploadParams(ToolParams):
    element_id: str
    resource_names: List[str]  # Support multiple files

class UploadTool(Tool):
    """Tool for uploading files to input elements."""

    def __init__(self, llm_browser: LLMBrowser, agent: Agent):
        self.llm_browser = llm_browser
        self.agent = agent  # Need reference to access resources

    async def execute(self, params: UploadParams) -> ExecutionResult:
        """
        Execute file upload.

        Steps:
        1. Resolve resource names to file paths via agent.get_resource()
        2. Validate all files exist
        3. Call llm_browser.upload(element_id, file_paths)
        """
```

### 3. LLMBrowser Upload Method

**File**: `llm_browser/llm_browser.py`

```python
async def upload(self, element_id: str, file_paths: List[str]) -> None:
    """
    Upload files to input element.

    Args:
        element_id: Element ID from DOM (e.g., "input-0")
        file_paths: List of absolute file paths to upload

    Raises:
        ValueError: If element_id not found in element_map
        RuntimeError: If file upload fails
    """
    # Convert element_id -> XPath -> Element
    # Call element.set_input_files(file_paths)
```

### 4. Page/Element Interface

**Note**: Playwright already supports this via `element.set_input_files()`. Just need to expose it through our abstraction layers:

**File**: `browser/element.py`

```python
async def set_input_files(self, files: List[str]) -> None:
    """Upload files to input element."""
```

**File**: `integrations/browser/playwright/playwright_element.py`

```python
async def set_input_files(self, files: List[str]) -> None:
    """Upload files to input element."""
    await self._element.set_input_files(files)
```

### 5. Prompt Updates

**File**: `prompts_data/agent/proposer.yaml`

Include available resources in the proposer context so the LLM knows what files are available:

```yaml
system: |
  ...

  {% if resources %}
  Available resources for upload:
  {% for name, path in resources.items() %}
  - {{ name }}: {{ path }}
  {% endfor %}
  {% endif %}
```

---

## Alternative: Task-Scoped Resources

If resources should be tied to specific tasks rather than persisting on the agent:

```python
result = await agent.execute(
    task="upload product images",
    resources={
        "image1": "/path/to/img1.jpg",
        "image2": "/path/to/img2.jpg"
    }
)
```

**Pros**:
- Cleaner for one-off tasks
- Resources automatically scoped to task lifecycle

**Cons**:
- Less flexible for multi-step workflows
- Can't pre-configure resources once and reuse

---

## Open Questions

1. **Scope preference**: Agent-scoped (persistent) or task-scoped (per-execute call)?
2. **Validation**: Should we validate that file paths exist when adding resources?
3. **Resource types**: Just files, or should we support URLs too (download then upload)?
4. **Naming**: `add_resource` / `set_resources` or something else like `register_file`?
5. **Tool registration**: UploadTool needs agent reference - how to handle circular dependency?

---

## Next Steps

1. Decide on scope (agent-scoped vs task-scoped)
2. Implement Agent resource management methods
3. Implement UploadTool
4. Add upload method to LLMBrowser
5. Expose set_input_files through Element interface
6. Update proposer prompts to include available resources
7. Write tests
8. Update documentation and examples
