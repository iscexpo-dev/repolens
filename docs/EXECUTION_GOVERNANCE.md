# Execution Governance

This policy governs the requirement inventory in `100_PERCENT_COVERAGE_MASTER_TODO.md` and its machine-readable mirror in `PROGRESS_STATE.json`. The TODO is the scope/acceptance source; the JSON file is the execution checkpoint. Update both together whenever a task state changes.

## Task States and Transitions

- `TODO`: not started or returned to the queue. It may move to `IN_PROGRESS`, `DEFERRED`, or `CANCELED` when the recorded reason and approval rules below are satisfied.
- `IN_PROGRESS`: an owner has selected the task, recorded intended files and acceptance criteria, and is actively working. It may move to `DONE`, `BLOCKED`, `TODO`, `DEFERRED`, or `CANCELED`.
- `BLOCKED`: progress depends on a named missing input, unresolved prerequisite, authorization, or safety condition. Record the smallest resolving action and continue independent tasks. It may return to `IN_PROGRESS` when the blocker is removed, or move to `DEFERRED`/`CANCELED` under the rules below.
- `DONE`: every acceptance criterion is satisfied and evidence is recorded. This is not a planning label. It may be reopened to `TODO` or `IN_PROGRESS` only when new evidence invalidates the prior completion or an acceptance criterion changes; preserve the former evidence and explain the reopening.
- `DEFERRED`: intentionally removed from the active milestone with rationale, owner, and approval when the deferral changes approved scope. It may return to `TODO`/`IN_PROGRESS` when the deferral expires or scope is approved again.
- `CANCELED`: invalidated or removed from scope by a recorded decision explaining why. It is terminal unless a new decision creates/reinstates the requirement; do not silently reactivate it.

Every transition records the previous/new state, timestamp in UTC, actor, rationale, and linked evidence or blocker. A task cannot be marked `DONE` while a required dependency is unresolved unless an explicit alternative dependency is documented and accepted.

## Completion Evidence

A `DONE` task must link to the artifact or decision that meets each acceptance criterion and to proportionate verification evidence: exact command, exit code, summary, and run time for executable checks; code/document path and reviewed acceptance points for non-executable work; and adjudicated or authorized decision records where appropriate. Preserve failed runs and distinguish tests that did not start from tests that ran and failed. A green suite does not prove unrelated task acceptance. Code presence, an unchecked plan, agent assertion, or target metric is not evidence by itself.

For benchmark or quality claims, additionally preserve immutable dataset/configuration identity, matching/judge method, sample counts, exclusions/failures, uncertainty, and the actual result artifacts. Mark missing evidence as `TODO` or `BLOCKED`, never infer success.

## Dependency and Critical-Path Policy

Dependencies are directed prerequisites. The task graph must be acyclic; a cycle is a planning error to resolve before execution, not permission to ignore prerequisites. Before selecting work, validate dependency IDs and identify ready tasks whose dependencies are satisfied. Prefer P0 over P1 over P2 among ready tasks, then prioritize phase gates and the longest critical path. A prerequisite marked `BLOCKED`, `TODO`, or `IN_PROGRESS` keeps dependent work unavailable unless an accepted alternative is recorded.

When a task becomes blocked, identify its direct and transitive descendants in each affected task's `dependency_waiting_on` array in `PROGRESS_STATE.json`, listing the unresolved prerequisite task IDs. Do not change a descendant's task state unless it was actively selected and cannot proceed. Continue unrelated ready tasks. Re-evaluate readiness after every dependency transition and clear resolved IDs from the array. Do not mark a parent done solely to unblock descendants.

## Architecture Decision Records

Use `docs/adr/README.md` and `docs/adr/0000-template.md` for material architecture decisions. ADRs are numbered, immutable decision history: supersede an accepted ADR with a new record rather than rewriting its decision. Link affected task IDs and update the risk/decision registers when a choice creates material consequences. Minor implementation choices that do not affect interfaces, security, operations, data, or long-term reversibility do not need an ADR.
