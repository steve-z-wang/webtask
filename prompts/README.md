# Prompts Directory

This directory contains all LLM prompts used in the webtask system.

## Structure

```
prompts/
├── agent/              # Agent role prompts
│   ├── proposer.yaml   # Proposer agent prompts
│   └── verifier.yaml   # Verifier agent prompts
└── selector/           # Element selector prompts
    └── natural_selector.yaml
```

## Format

Each YAML file contains prompts with the following structure:

```yaml
prompt_key:
  description: "Human-readable description of the prompt's purpose"
  content: |
    The actual prompt text...
```

## Usage

Prompts are accessed via the `PromptLibrary` class:

```python
from webtask.prompts import get_prompt

# Get a prompt by key
system_prompt = get_prompt("proposer_system")
```

## Available Prompts

| Key | File | Purpose |
|-----|------|---------|
| `proposer_system` | `agent/proposer.yaml` | Proposer agent system prompt |
| `verifier_system` | `agent/verifier.yaml` | Verifier agent system prompt |
| `selector_system` | `selector/natural_selector.yaml` | Natural element selector prompt |

## Guidelines

1. **Keep prompts focused**: Each prompt should have a clear, single purpose
2. **Use descriptive keys**: Keys should clearly indicate what the prompt does
3. **Document changes**: Update this README when adding new prompts
4. **Test thoroughly**: Changes to prompts can significantly affect agent behavior
5. **Version control**: Commit prompt changes separately from code changes when possible

## Modifying Prompts

To modify a prompt:

1. Edit the relevant YAML file
2. Test the changes thoroughly
3. Document any behavioral changes in commit messages
4. Consider A/B testing for significant changes

Note: Prompts are loaded once and cached in memory. To reload prompts during development, restart the application or use `PromptLibrary.reload()`.
