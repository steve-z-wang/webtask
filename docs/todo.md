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

## Future Work
- [ ] Add more browser actions (scroll, hover, upload_file)
- [ ] Implement retry logic for failed actions
- [ ] Add screenshot capture on errors
- [ ] Support for multi-page tasks
- [ ] Optimize token usage
- [ ] Add logging/tracing for debugging
