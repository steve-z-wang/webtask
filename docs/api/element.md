
# Element

Abstract base class for browser element.

Simple adapter over browser automation library elements (Playwright, Selenium, etc.). Typically obtained via `agent.select()` or `page.select_one()`.


### `fill()`

```python
async def fill(text: str)
```

Fill the element with text (for input fields). Sets value instantly.

**Parameters:**
- `text` (str): Text to fill

**Example:**
```python
input_field = await agent.select("email input")
await input_field.fill("user@example.com")
```


### `upload_file()`

```python
async def upload_file(file_path: Union[str, List[str]])
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


## Comparison: fill() vs type()

```python
# fill() - Instant, direct value setting
await input_field.fill("web automation")  # Fast

# type() - Character-by-character with delays
await input_field.type("web automation", delay=80)  # Slower, more realistic
```

Use `fill()` for speed, `type()` for simulating human-like interaction.
