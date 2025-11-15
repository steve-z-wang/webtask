# Test Fixtures - Recording & Replay

This directory contains recorded test fixtures for deterministic end-to-end testing.

## Structure

```
fixtures/
├── llm/           # Recorded LLM interactions (prompts and responses)
│   └── *.json
└── browser/       # Recorded browser interactions (DOM snapshots, screenshots, etc.)
    └── *.json
```

## How It Works

### Recording Mode

Run tests with `WEBTASK_TEST_MODE=record` to capture interactions:

```bash
WEBTASK_TEST_MODE=record pytest tests/e2e/test_recording_example.py
```

This will:
1. Execute tests against real LLM APIs and live websites
2. Record all LLM prompts/responses to `fixtures/llm/*.json`
3. Record all browser interactions to `fixtures/browser/*.json`
4. Create fixture files automatically

### Replay Mode

Run tests with `WEBTASK_TEST_MODE=replay` for fast, deterministic testing:

```bash
WEBTASK_TEST_MODE=replay pytest tests/e2e/test_recording_example.py
```

This will:
1. Load recorded interactions from fixture files
2. Return saved responses without calling LLM APIs (free!)
3. Return saved browser states without network requests (offline!)
4. Execute much faster than live tests
5. Produce identical results every time

### Live Mode

Run tests without `WEBTASK_TEST_MODE` for normal operation:

```bash
pytest tests/e2e/test_recording_example.py
```

This bypasses recording/replay entirely (useful for updating tests).

## Benefits

- **Zero API Costs**: Replay mode doesn't call LLM APIs
- **Offline Testing**: No network requests needed
- **Deterministic**: Same inputs always produce same outputs
- **Fast Execution**: Replay is much faster than live tests
- **CI/CD Friendly**: No API keys or credentials needed for replay

## Fixture Management

### Creating New Fixtures

1. Write your test using `RecordingLLM` and `RecordingBrowser`
2. Run once in record mode: `WEBTASK_TEST_MODE=record pytest tests/e2e/test_your_test.py`
3. Commit the generated fixture files to git
4. Future test runs use replay mode by default

### Updating Fixtures

When behavior changes (e.g., prompt updates, website changes):

1. Delete old fixture files
2. Re-record: `WEBTASK_TEST_MODE=record pytest tests/e2e/test_your_test.py`
3. Review and commit updated fixtures

### Fixture Size

Browser fixtures can be large (DOM snapshots, screenshots). Consider:
- Using `.gitattributes` with LFS for large fixtures
- Keeping browser interactions minimal in tests
- Splitting large tests into smaller ones

## Example Test

```python
from webtask.testing import RecordingLLM, RecordingBrowser
from webtask.integrations.llm import GeminiLLM
from webtask.integrations.browser.playwright import PlaywrightBrowser

@pytest.mark.asyncio
async def test_example():
    # Setup
    llm = RecordingLLM(
        llm=GeminiLLM.create(...),
        fixture_path="tests/e2e/fixtures/llm/example.json"
    )
    browser = RecordingBrowser(
        browser=await PlaywrightBrowser.create(...),
        fixture_path="tests/e2e/fixtures/browser/example.json"
    )

    # Test runs in record/replay/live mode based on env var
    # ...
```

## Notes

- Fixtures are environment-specific (check your .env file)
- Record mode requires real API keys and network access
- Replay mode works completely offline
- Fixture format is JSON for easy inspection and debugging
