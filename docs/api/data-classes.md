
# Data Classes

**Result** - Returned by `agent.do()`

```python
@dataclass
class Result:
    status: Optional[Status]
    output: Optional[Any]
    feedback: Optional[str]
```

**Verdict** - Returned by `agent.verify()`

```python
@dataclass
class Verdict:
    passed: bool
    feedback: str
    status: Status
```

Can be used as boolean:

```python
verdict = await agent.verify("the cart contains 2 items")

if verdict:
    print("Success!")
```

**Status** - Task status enum

```python
class Status(str, Enum):
    COMPLETED = "completed"
    ABORTED = "aborted"
```
