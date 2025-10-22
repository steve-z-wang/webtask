# TODO

## Testing

### 1. Manual Testing
- [ ] Test high-level autonomous mode (`agent.execute()`)
  - [ ] Simple navigation tasks
  - [ ] Form filling tasks
  - [ ] Multi-step workflows
- [ ] Test low-level imperative mode
  - [ ] `agent.navigate()`
  - [ ] `agent.select()` with various element descriptions
  - [ ] Chaining element actions (`.click()`, `.fill()`)
- [ ] Test error handling
  - [ ] Invalid element descriptions
  - [ ] Failed actions
  - [ ] Max steps reached
- [ ] Test different LLM providers
  - [ ] OpenAI
  - [ ] Gemini

### 2. Mind2Web v1 Evaluation
- [ ] Set up Mind2Web dataset
- [ ] Create evaluation harness
- [ ] Run on Mind2Web test set
- [ ] Collect metrics
  - [ ] Task success rate
  - [ ] Element selection accuracy
  - [ ] Step efficiency
- [ ] Analyze failure cases
- [ ] Document findings

## Recently Completed
- [x] Add logging/tracing for debugging (LLM calls, token usage)
- [x] Support for multi-tab tasks (new_tab, switch_tab, close_tab)
- [x] Add wait methods (wait, wait_for_idle)
- [x] Webtask manager for browser lifecycle management
- [x] XPath-based element selection using original DOM
- [x] Multi-provider LLM support (OpenAI, Gemini) with logging

## Future Work
- [ ] Add more browser actions (scroll, hover, upload_file)
- [ ] Implement retry logic for failed actions
- [ ] Add screenshot capture on errors
- [ ] Optimize token usage
- [ ] Vision-based element selection (Set-of-Marks approach)
- [ ] CAPTCHA handling strategies
