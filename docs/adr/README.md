# Architecture Decision Records

Record material architecture decisions in this directory using `0000-template.md`.

1. Copy the template to the next zero-padded sequence number and a short kebab-case title, for example `0001-model-provider-boundary.md`.
2. Set a unique ADR ID, UTC date, owner, status, and affected task IDs. Describe the context and constraints before comparing realistic alternatives, including a do-nothing option when relevant.
3. Record one explicit decision, its consequences/trade-offs, security and operations implications, and evidence or validation still required. Keep proposals labeled proposed; do not imply approval.
4. Review material decisions with the accountable project owner and relevant engineering/security/benchmark/operations owners. Record who accepted it and when.
5. Once accepted, do not rewrite its decision history. Mark it superseded and link the replacing ADR when a later decision changes it. Keep rejected proposals when they explain a consequential choice.
6. Link the ADR from affected tasks and record resulting risks, blockers, or required follow-up work in `PROGRESS_STATE.json`.

An ADR records a decision; it does not replace implementation, testing, security review, or benchmark evidence.
