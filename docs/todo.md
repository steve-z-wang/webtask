# TODO

## Testing Infrastructure

### 1. Create Recording/Replayable End-to-End Tests

Implement E2E test infrastructure with LLM response recording/replay:

- [ ] Create `RecordedLLM` class in `tests/e2e/recorded_llm.py`
  - Implements `LLM` base class
  - Records LLM responses to cassette files in RECORD mode
  - Replays saved responses in default mode (no API calls)
- [ ] Add `is_record_mode()` helper in `tests/conftest.py`
  - Reads `WEBTASK_RECORD` environment variable
- [ ] Create example E2E test (e.g., `tests/e2e/test_navigation.py`)
  - Tests basic navigation task
  - Uses `recorded_llm` fixture
- [ ] Add cassettes directory to git (`.gitignore` cassettes with large files)
- [ ] Document workflow in README:
  - Recording: `WEBTASK_RECORD=1 pytest tests/e2e/`
  - Replaying: `pytest tests/e2e/` (no API key needed)

**Benefits:**
- Fast, deterministic tests
- No API costs for CI/teammates
- Easy debugging (inspect cassette JSON)

### 2. Test on Mind2Web Dataset

Benchmark webtask against Mind2Web evaluation dataset:

- [ ] Download Mind2Web dataset
- [ ] Create benchmark script (`benchmarks/mind2web.py`)
- [ ] Implement evaluation metrics (success rate, step efficiency)
- [ ] Run baseline evaluation
- [ ] Document results in `docs/benchmarks/mind2web.md`

**Mind2Web Info:**
- Dataset: https://github.com/OSU-NLP-Group/Mind2Web
- Real-world web tasks across multiple domains
- Standard benchmark for web agents
