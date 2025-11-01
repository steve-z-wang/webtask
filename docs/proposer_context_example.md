# Proposer Context Example

This shows the exact context sent to the LLM in the new single-call architecture.

## Context Structure

```
Context:
  - System Prompt (proposer_system)
  - User Blocks:
    1. Task
    2. Step History
    3. Available Tools
    4. Current Page State (text + screenshot)
```

---

## Example: "Fill the price as $50 and submit"

### Step 1 Context (First Action)

```
=== SYSTEM PROMPT ===
You are a web automation agent. Your task is to propose the next actions AND determine if the task is complete.

You will receive:
- The task to accomplish
- Step history (previous actions and results)
- Available tools and their schemas
- Current page state with element IDs

You must respond with a JSON object containing:
{
  "complete": true/false,
  "message": "Explanation of task status",
  "actions": [...]
}

## Decision Flow

**FIRST: Check if task is complete**
1. Re-read the original task - What EXACTLY was requested?
2. Check current page state - Does it show the task is done?
3. Review step history - Were previous actions successful?
4. Verify ALL requirements - Is every part of the task satisfied?

**THEN: Decide on actions**
- If complete=true: Return empty actions []
- If complete=false: Return next actions to take

[... rest of proposer_system prompt ...]

=== USER MESSAGE ===

Task:
Fill the price as $50 and submit

---

Step History:
No steps executed yet.

---

Available Tools:

Tool: navigate
Description: Navigate to a URL
Parameters:
  - url (string, required): URL to navigate to

Tool: click
Description: Click an element
Parameters:
  - element_id (string, required): Element ID to click

Tool: fill
Description: Fill a form field
Parameters:
  - element_id (string, required): Element ID to fill
  - value (string, required): Value to fill

Tool: type
Description: Type into an element with keyboard simulation
Parameters:
  - element_id (string, required): Element ID to type into
  - value (string, required): Text to type

---

Current Page State:

- html
  - body
    - div
      - form
        - label-0 (aria-label="Price")
          - "Price"
        - input-0 (type="text" name="price" placeholder="Enter price")
        - button-0 (type="submit")
          - "Submit"

[SCREENSHOT WITH BOUNDING BOXES]
```

### Step 1 Response

```json
{
  "complete": false,
  "message": "Need to fill price field and submit form",
  "actions": [
    {
      "reason": "Fill the price field with $50",
      "tool": "fill",
      "parameters": {
        "element_id": "input-0",
        "value": "50"
      }
    },
    {
      "reason": "Submit the form",
      "tool": "click",
      "parameters": {
        "element_id": "button-0"
      }
    }
  ]
}
```

---

### Step 2 Context (After Execution)

```
=== SYSTEM PROMPT ===
[Same as before]

=== USER MESSAGE ===

Task:
Fill the price as $50 and submit

---

Step History:

Step 1:
  Status: Incomplete
  Message: Need to fill price field and submit form
  Action 1:
    Tool: fill
    Reason: Fill the price field with $50
    Parameters: {'element_id': 'input-0', 'value': '50'}
    Execution: Success
  Action 2:
    Tool: click
    Reason: Submit the form
    Parameters: {'element_id': 'button-0'}
    Execution: Success

---

Available Tools:
[Same as before]

---

Current Page State:

- html
  - body
    - div
      - h1
        - "Success!"
      - p
        - "Your listing has been created with price $50"
      - a-0 (href="/listings")
        - "View all listings"

[SCREENSHOT SHOWING SUCCESS PAGE]
```

### Step 2 Response

```json
{
  "complete": true,
  "message": "Task completed successfully: Price filled as $50 and form submitted. Success page confirms the listing was created.",
  "actions": []
}
```

---

## Key Observations

### 1. **Step History Grows Over Time**
Each step adds to the history, so the proposer can see:
- What actions were tried
- Whether they succeeded or failed
- What verification messages were given

### 2. **Page State Reflects Previous Actions**
After filling and submitting:
- Page shows success message
- Form is no longer visible
- Proposer can verify completion by seeing the success state

### 3. **Proposer Makes Both Decisions**
In the same response, it:
- Checks if task is complete (by examining history + page state)
- Proposes next actions (if not complete) OR returns empty actions (if complete)

### 4. **Context Size**
- **System prompt**: ~1.5k tokens (proposer_system)
- **Task**: ~20 tokens
- **Step history**: Grows with each step (~200 tokens per step)
- **Tools**: ~300 tokens
- **Page state**: 500-2000 tokens (depends on page complexity)
- **Screenshot**: Varies (if enabled, adds image tokens)

**Total per step**: ~2-5k tokens input

---

## Comparison: Old vs New Context

### Old Architecture (2 LLM Calls)

**Proposer Context:**
```
System: proposer_system
User:
  - Task
  - Step History (without current step)
  - Tools
  - Page State
```
→ Returns: `actions[]`

**Verifier Context:**
```
System: verifier_system
User:
  - Task
  - Current Actions + Execution Results
  - Step History (without current step)
  - Page State (FETCHED AGAIN after execution)
```
→ Returns: `{complete, message}`

**Total**: 2 LLM calls, 2 page snapshots, 2 screenshots

### New Architecture (1 LLM Call)

**Proposer Context:**
```
System: proposer_system (enhanced with verification logic)
User:
  - Task
  - Step History (includes previous execution results)
  - Tools
  - Page State
```
→ Returns: `{complete, message, actions[]}`

**Total**: 1 LLM call, 1 page snapshot, 1 screenshot

---

## Context Cost Analysis

### Example 10-step task:

**Old Architecture:**
- Step 1: Proposer (3k tokens) + Verifier (3k tokens) = 6k
- Step 2: Proposer (3.2k) + Verifier (3.2k) = 6.4k
- ...
- Step 10: Proposer (5k) + Verifier (5k) = 10k

**Total**: ~75k input tokens

**New Architecture:**
- Step 1: Proposer (3k tokens)
- Step 2: Proposer (3.2k tokens)
- ...
- Step 10: Proposer (5k tokens)

**Total**: ~40k input tokens

**Savings**: 47% reduction in input tokens (even accounting for slightly larger prompts)

---

## Why This Works

The proposer sees **the same information** the verifier would have seen:

1. **Task requirements** ✓ (same)
2. **Current page state** ✓ (same - fetched after previous execution)
3. **Previous execution results** ✓ (in step history)
4. **History of all steps** ✓ (same)

The only difference is **timing**:
- Old: Verifier checks completion AFTER current step executes
- New: Proposer checks completion BEFORE proposing next step

But since the proposer sees the results of the **previous** step's execution in the page state and history, it has everything needed to determine completion!
