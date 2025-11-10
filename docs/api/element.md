
# Element

Abstract base class for browser element.

Simple adapter over browser automation library elements (Playwright, Selenium, etc.). Typically obtained via `agent.select()` or `page.select_one()`.

## Action Methods

### `click()`

```python
async def click() -> None
```

Click the element.

**Example:**
```python
button = await agent.select("submit button")
await button.click()
```

### `fill()`

```python
async def fill(text: str) -> None
```

Fill the element with text (for input fields). Sets value instantly.

**Parameters:**
- `text` (str): Text to fill

**Example:**
```python
input_field = await agent.select("email input")
await input_field.fill("user@example.com")
```

### `type()`

```python
async def type(text: str, delay: float = None) -> None
```

Type text into the element character by character.

**Parameters:**
- `text` (str): Text to type
- `delay` (float): Delay between keystrokes in milliseconds (None = instant)

**Example:**
```python
input_field = await agent.select("search box")
await input_field.type("web automation", delay=80)  # More realistic
```

**Comparison: fill() vs type()**
```python
# fill() - Instant, direct value setting
await input_field.fill("web automation")  # Fast

# type() - Character-by-character with delays
await input_field.type("web automation", delay=80)  # Slower, more realistic
```

Use `fill()` for speed, `type()` for simulating human-like interaction.

### `upload_file()`

```python
async def upload_file(file_path: Union[str, List[str]]) -> None
```

Upload file(s) to a file input element.

**Parameters:**
- `file_path` (Union[str, List[str]]): Single file path (str) or multiple file paths (List[str])

**Example:**
```python
# Single file
file_input = await agent.select("file upload input")
await file_input.upload_file("/path/to/file.pdf")

# Multiple files
await file_input.upload_file([
    "/path/to/file1.pdf",
    "/path/to/file2.png"
])
```

## Inspection Methods

### `get_tag_name()`

```python
async def get_tag_name() -> str
```

Get the tag name of the element.

**Returns:** Tag name (e.g., 'input', 'button', 'a')

**Example:**
```python
element = await agent.select("submit button")
tag = await element.get_tag_name()
print(f"Tag: {tag}")  # "button"
```

### `get_attribute()`

```python
async def get_attribute(name: str) -> Optional[str]
```

Get an attribute value from the element.

**Parameters:**
- `name` (str): Attribute name (e.g., 'type', 'id', 'class')

**Returns:** Attribute value or None if not present

**Example:**
```python
input_field = await agent.select("email input")
input_type = await input_field.get_attribute("type")
print(f"Input type: {input_type}")  # "email"

placeholder = await input_field.get_attribute("placeholder")
```

### `get_attributes()`

```python
async def get_attributes() -> Dict[str, str]
```

Get all attributes from the element.

**Returns:** Dictionary of attribute name-value pairs

**Example:**
```python
element = await agent.select("submit button")
attrs = await element.get_attributes()

print(f"ID: {attrs.get('id')}")
print(f"Class: {attrs.get('class')}")
print(f"Type: {attrs.get('type')}")
```

### `get_html()`

```python
async def get_html(outer: bool = True) -> str
```

Get the HTML content of the element.

**Parameters:**
- `outer` (bool): If True, returns outerHTML (includes the element itself). If False, returns innerHTML (only the element's content)

**Returns:** HTML string

**Example:**
```python
element = await agent.select("main content div")

# Get outer HTML (includes the div tag)
outer_html = await element.get_html(outer=True)

# Get inner HTML (only the content inside the div)
inner_html = await element.get_html(outer=False)
```

### `get_parent()`

```python
async def get_parent() -> Optional[Element]
```

Get the parent element.

**Returns:** Parent Element or None if no parent (e.g., root element)

**Example:**
```python
button = await agent.select("submit button")
parent = await button.get_parent()

if parent:
    parent_tag = await parent.get_tag_name()
    print(f"Parent tag: {parent_tag}")
```

### `get_children()`

```python
async def get_children() -> List[Element]
```

Get all direct child elements.

**Returns:** List of child Elements (may be empty)

**Example:**
```python
container = await agent.select("main navigation")
children = await container.get_children()
print(f"Number of children: {len(children)}")

for child in children:
    tag = await child.get_tag_name()
    print(f"  Child: {tag}")
```

## Complete Example

```python
from webtask import Webtask
from webtask.integrations.llm import GeminiLLM

async def main():
    wt = Webtask(headless=False)
    llm = GeminiLLM.create(model="gemini-2.5-flash")
    agent = await wt.create_agent(llm=llm)

    await agent.navigate("https://example.com")

    # Select element
    input_field = await agent.select("email input")

    # Inspect element
    tag = await input_field.get_tag_name()
    attrs = await input_field.get_attributes()
    print(f"Tag: {tag}, Attributes: {attrs}")

    # Interact with element
    await input_field.type("user@example.com", delay=80)

    # Click submit
    button = await agent.select("submit button")
    await button.click()

    await wt.close()
```
