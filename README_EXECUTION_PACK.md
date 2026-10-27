# Best AI Code Reviewer 2026 — Execution Pack

## Contents

- `100_PERCENT_COVERAGE_MASTER_TODO.md` — source-of-truth requirement and acceptance inventory.
- `AGENT_SUBMISSION_PROMPT.md` — copy-paste prompt for a long-running coding agent.
- `PROGRESS_STATE.json` — resumable task state, verified baseline, risks, and next actions.
- `FINAL_REPORT_TEMPLATE.md` — final implementation/benchmark/security report template.
- `MASTER_PLAN.md` and `docs/` — prior design plan, initial benchmark protocol, and security boundaries.
- `src/` and `tests/` — existing scaffold, not a completed reviewer.

## Current state

On 2026-10-24, `python -m pytest -q` passed 7 tests in the starter. No AI provider is configured; no end-to-end review benchmark or production integration is claimed.

## Start

Open this directory in your coding agent and paste `AGENT_SUBMISSION_PROMPT.md`. The agent should inspect and verify the repo, then update `PROGRESS_STATE.json` as it works. Do not treat a planned task or target metric as achieved until evidence exists.
