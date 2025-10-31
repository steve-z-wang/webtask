# TODO

## Testing

### 1. Unit Tests
- [ ] Core utilities
  - [ ] `utils/json_parser.py` - Test JSON parsing with malformed input
  - [ ] `utils/url.py` - Test URL normalization
  - [ ] `utils/wait.py` - Test wait function
- [x] DOM processing
  - [x] `dom/parsers/cdp.py` - Test CDP parser and helper functions (23 tests)
  - [x] `dom/filters/` - Test visibility and semantic filters (110 tests)
    - [x] Visibility filters: css_hidden, no_layout, non_visible_tags, zero_dimensions
    - [x] Semantic filters: attributes, empty, presentational, wrappers
    - [x] Filter orchestrators: apply_visibility_filters, apply_semantic_filters
  - [ ] `dom/serializers.py` - Test DOM to markdown serialization
- [ ] LLM context
  - [ ] `llm/context.py` - Test Block and Context building
  - [ ] `agent/step.py` - Test Action, ExecutionResult, VerificationResult data classes

### 2. Integration Tests
- [ ] LLM integration (with mocked responses)
  - [ ] Proposer returns valid Action objects
  - [ ] Verifier returns valid VerificationResult
  - [ ] Error handling for invalid LLM JSON responses
  - [ ] Token counting and limits
- [ ] Browser integration (with mocked Playwright)
  - [ ] PlaywrightPage methods (navigate, select, click, screenshot)
  - [ ] XPath-based element selection
  - [ ] wait_for_idle behavior
- [ ] Selector integration
  - [ ] Natural language selector with mocked LLM
  - [ ] Element ID mapping and XPath generation

### 3. End-to-End Tests
- [ ] Set up local test server with static HTML files
- [ ] Simple workflows
  - [ ] Navigate → select → click → verify
  - [ ] Form filling and submission
  - [ ] Multi-step tasks
  - [ ] Screenshot capture
- [ ] Step-by-step execution mode
  - [ ] set_task() and execute_step() loop
  - [ ] Progress tracking
- [ ] Error scenarios
  - [ ] Element not found
  - [ ] Navigation failures
  - [ ] Timeout handling

### 4. Benchmark Evaluation
- [ ] Mind2Web v1
  - [ ] Set up Mind2Web dataset
  - [ ] Create evaluation harness
  - [ ] Run on Mind2Web test set
  - [ ] Collect metrics (success rate, element accuracy, step efficiency)
  - [ ] Analyze failure cases
  - [ ] Document findings
- [ ] WebArena
  - [ ] Set up WebArena environment
  - [ ] Run benchmark suite
  - [ ] Track performance over time

### 5. Test Infrastructure
- [x] Set up pytest with pytest-asyncio
- [x] Create fixtures for mocked LLM responses (conftest.py)
- [ ] Set up local HTTP server for test HTML files
- [x] Add pytest-mock for mocking dependencies
- [x] Set up GitHub Actions CI/CD pipeline (pr.yml, test.yml, publish.yml)
- [x] Add test coverage reporting (pytest-cov)
- [x] Add linting and formatting checks (ruff, black)
- [x] Create local PR check script (scripts/pr.sh)

## Recently Completed

### Manual Testing
- [x] Test high-level autonomous mode (agent.execute())
  - [x] Simple navigation tasks
  - [x] Form filling tasks
  - [x] Multi-step workflows (e-commerce shopping cart)
- [x] Test step-by-step execution mode
  - [x] agent.set_task() and agent.execute_step()
  - [x] Progress tracking and debugging
  - [x] Custom control flow with step results
- [x] Test low-level imperative mode
  - [x] agent.navigate()
  - [x] agent.select() with various element descriptions
  - [x] Chaining element actions (.click(), .fill(), .type())
  - [x] agent.screenshot() for capturing page states
- [x] Test error handling
  - [x] Invalid element descriptions
  - [x] Failed actions
  - [x] Max steps reached
  - [x] Empty actions from proposer
- [x] Test different LLM providers
  - [x] OpenAI (gpt-4.1, gpt-4.1-mini, gpt-5-nano)
  - [x] Gemini (gemini-2.5-flash)

### Features
- [x] Step-by-step execution mode (set_task, execute_step, clear_history)
- [x] Screenshot support (agent.screenshot, page.screenshot)
- [x] Action delays for page loading (configurable action_delay)
- [x] Wait utility function (utils/wait.py)
- [x] Context formatting improvements (section titles, proper newlines)
- [x] Full debug logging (no truncation of prompts/responses)
- [x] Support for new OpenAI models (gpt-4.1, gpt-4.1-mini, gpt-5-nano)
- [x] Jupyter notebook examples with screenshots
- [x] Add logging/tracing for debugging (LLM calls, token usage)
- [x] Support for multi-page tasks (open_page, close_page, set_page, get_pages)
- [x] Flexible page/session initialization (support existing browsers)
- [x] Add wait methods (wait, wait_for_idle)
- [x] Webtask manager for browser lifecycle management
- [x] XPath-based element selection using original DOM
- [x] Multi-provider LLM support (OpenAI, Gemini) with logging

## Future Work
- [ ] Add more browser actions (scroll, hover, upload_file)
- [ ] Implement retry logic for failed actions
- [ ] Add automatic screenshot capture on errors
- [ ] Optimize token usage (compress DOM, cache common elements)
- [ ] Vision-based element selection (Set-of-Marks approach)
- [ ] CAPTCHA handling strategies
- [ ] Rate limiting and automatic backoff for LLM APIs
- [ ] Configurable page wait strategies (custom conditions, selectors)
