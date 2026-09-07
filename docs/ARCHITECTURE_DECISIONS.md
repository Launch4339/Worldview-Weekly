# Worldview Weekly — Architecture Decisions

## 2026-09-07 — Keep the native ChatGPT weekly schedule for now

### Decision
Keep the recurring **Counterweight Thursday** job as a native ChatGPT scheduled task. Do **not** migrate its schedule to GitHub Actions or another external cron at this time.

This is a deliberate decision against speculative automation. The current native schedule is simple, already works, and preserves the important behavior: when the job runs, ChatGPT performs a fresh intelligent reassessment of the recent candidate pool and chooses the issue dynamically.

### Proposal considered
A future migration could separate the clock from the editorial intelligence:

1. GitHub Actions (or another simple external scheduler) fires on Thursday.
2. The scheduler emits only a minimal wake signal to the shared global ChatGPT execution/coordinator path.
3. ChatGPT, using the appropriate capable model, performs the full Worldview Weekly run-time work: searches roughly the prior 7–14 days, evaluates importance and quality, applies source/viewpoint/geographic/accessibility rules, chooses the ~12 articles for that specific week, writes the issue and full-depth audio synthesis, and publishes to the existing Worldview Weekly repository.
4. GitHub remains a clock/publishing substrate only. It must **not** contain a deterministic article picker, static source quota engine, or outsourced editorial logic.

In short: **external cron may eventually provide the wake-up, but ChatGPT must continue to provide the editorial judgment.**

### Why the migration is rejected for now
The only material benefit today would be freeing one ChatGPT scheduled-task slot. That benefit is not yet large enough to justify adding another dependency chain and failure surface.

The apparent slot pressure is currently inflated by temporary Global Execution Architecture v2 battle-test tasks. Once those temporary tasks retire, the persistent scheduled-task footprint should be much smaller. Moving Worldview Weekly now would therefore be automation for automation's sake rather than a response to an observed recurring constraint.

The migration would also depend on the shared global event/coordinator path, which should not be treated as production infrastructure for Readings until it has been fully proven end-to-end.

### Reconsideration criteria
Reconsider this decision only when **all three** conditions are true:

1. The shared Global Execution Coordinator/event path is durably proven operational and reliable, rather than still being battle-tested.
2. ChatGPT scheduled-task scarcity is a real ongoing constraint — for example, the account is approaching the permanent active-task limit and Worldview Weekly is blocking a more valuable recurring use.
3. External scheduling has become a standard shared capability, so adding one more weekly wake-up is a low-maintenance reuse of existing infrastructure rather than a bespoke Readings automation project.

If those conditions are met, Worldview Weekly is a good migration candidate because it naturally separates into a dumb external clock plus intelligent ChatGPT execution.

### Override
The user explicitly reserves the right to request this migration at any time. An explicit future user request overrides the default hold decision above, even if the criteria have not all been met.

### Default operating rule
Until either the reconsideration criteria are met or the user explicitly asks to proceed, **do not reopen or re-propose this migration merely to save a slot**. Keep Counterweight Thursday native and focus on the quality and reliability of the reading experience.
