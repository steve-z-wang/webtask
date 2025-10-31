# Development Scripts

## Using PDM (Recommended)

```bash
# Run all PR checks (lint + format-check + tests)
pdm run pr

# Auto-fix issues then run checks
pdm run pr-fix

# Individual commands
pdm run lint          # Run ruff linter
pdm run format        # Auto-format with black
pdm run format-check  # Check formatting without changes
pdm run test          # Run tests
pdm run test-cov      # Run tests with coverage report
```

## Using Scripts Directly

```bash
# Run all PR checks (same as CI)
./scripts/pr.sh

# Auto-fix issues then run checks
./scripts/pr.sh fix
```

## Workflow

Before committing:
1. `pdm run pr-fix` - Auto-fix any formatting/linting issues
2. `pdm run pr` - Verify all checks pass
3. Commit and push!
