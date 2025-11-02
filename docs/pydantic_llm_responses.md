# Pydantic LLM Response Models Plan

## Problem
Currently we manually parse LLM JSON responses with dict access and manual validation:
```python
response = await self.llm.generate(context, json_mode=True)
data = parse_json(response)
complete = data.get("complete")
message = data.get("message")
if complete is None or not message:
    raise ValueError(...)
```

This is error-prone and lacks type safety.

## Solution
Use Pydantic models for automatic validation and structured outputs.

## Changes Required

### 1. Convert step.py models to Pydantic

**Current (dataclass):**
```python
@dataclass
class Action:
    reason: str
    tool_name: str
    parameters: Dict[str, Any]

@dataclass
class ProposalResult:
    complete: bool
    message: str
    actions: List[Action]
```

**New (Pydantic):**
```python
from pydantic import BaseModel, Field

class ActionModel(BaseModel):
    """Action from LLM proposal."""
    reason: str = Field(description="Why this action is needed")
    tool: str = Field(description="Tool name to execute", alias="tool_name")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ProposerResponse(BaseModel):
    """Expected response format from proposer LLM."""
    complete: bool = Field(description="Whether task is complete")
    message: str = Field(description="Status explanation")
    actions: List[ActionModel] = Field(default_factory=list)
```

### 2. Add structured output support to LLM

**OpenAI:** Supports `response_format` with JSON schema
```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "proposer_response",
        "schema": ProposerResponse.model_json_schema()
    }
}
```

**Gemini:** Supports `response_schema` parameter
```python
from google.generativeai import protos
schema = ProposerResponse.model_json_schema()
response_schema = protos.Schema.from_dict(schema)
```

### 3. Update LLM base class

```python
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLM(ABC):
    async def generate(
        self,
        context: Context,
        response_model: Optional[Type[T]] = None
    ) -> str | T:
        """
        Generate response, optionally structured.

        Args:
            context: Context to generate from
            response_model: Optional Pydantic model for structured output

        Returns:
            String if no response_model, otherwise instance of response_model
        """
        ...
```

### 4. Update proposer to use structured output

**Before:**
```python
response = await self.llm.generate(context, json_mode=True)
data = parse_json(response)
complete = data.get("complete")
message = data.get("message")
# Manual validation...
```

**After:**
```python
response = await self.llm.generate(context, response_model=ProposerResponse)
# response is already a ProposerResponse with validated fields
# Access with response.complete, response.message, response.actions
```

### 5. Similar changes for selector

```python
class SelectorResponse(BaseModel):
    element_id: Optional[str] = Field(None, description="Matching element ID")
    error: Optional[str] = Field(None, description="Error if no match")
```

## Benefits

1. **Type safety** - IDE autocomplete, type checking
2. **Automatic validation** - Pydantic validates fields
3. **Cleaner code** - No manual dict parsing
4. **Better errors** - Pydantic gives detailed validation errors
5. **Documentation** - Field descriptions become part of schema
6. **Guaranteed structure** - LLM providers enforce schema at API level

## Migration Strategy

1. Convert step.py to Pydantic (maintain compatibility)
2. Add response_model parameter to LLM
3. Implement structured output in OpenAI/Gemini
4. Update proposer to use structured output
5. Update selector to use structured output
6. Consider deprecating json_mode in favor of response_model

## Compatibility Note

We need to ensure backward compatibility since other code uses these models. We can:
- Keep the same field names
- Use `Field(alias=...)` where LLM response format differs
- Add helper methods if needed for migration
