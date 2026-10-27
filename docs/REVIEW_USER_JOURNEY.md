# Core PR Review User Journey

**Status:** Product acceptance contract; this is a proposed workflow, not implemented integration behavior.

The sequence below describes the intended read-only journey. GitHub ingestion, immutable snapshot storage, model/tool execution, finding verification, result presentation, and feedback collection are not implemented in this repository today.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant Git as Git provider
    participant Ingest as Ingestion service (planned)
    participant Store as Immutable snapshot store (planned)
    participant Review as Review orchestrator (planned)
    participant Tools as Configured analyzers (planned)
    participant Model as Configured model provider (planned)
    participant Verify as Finding/evidence verifier (planned)
    participant UI as Read-only result surface (planned)
    participant Feedback as Feedback record (planned)
    participant Audit as Independent benchmark adjudication

    Dev->>Git: Open or update pull request
    Git-->>Ingest: Authorized PR event (authenticated and deduplicated)
    Ingest->>Git: Fetch base/head identities and diff
    Git-->>Ingest: PR metadata and content
    Ingest->>Store: Persist immutable snapshot(base SHA, head SHA, diff digest)
    Store-->>Ingest: Snapshot ID
    Ingest->>Review: Start run bound to snapshot ID and policy/config versions
    Review->>Review: Parse diff and classify changed paths/languages

    alt Input is incomplete, unsupported, or exceeds limits
        Review->>UI: Partial/unverified status and reason; no safety claim
    else Inputs are usable
        par Deterministic checks
            Review->>Tools: Run only configured, permitted analyzers
            Tools-->>Review: Findings, check status, version, or unavailable/error
        and Model analysis
            Review->>Model: Send minimum permitted diff/context as untrusted data
            Model-->>Review: Structured candidate findings or timeout/error
        end
        Review->>Verify: Candidates + exact snapshot + tool/check outcomes
        Verify->>Verify: Validate schema, evidence, changed-line anchors, policy, and duplicates
        alt Finding is supported and anchor is valid
            Verify-->>UI: Actionable finding with evidence and uncertainty
        else Finding is unsupported or anchor is invalid
            Verify-->>UI: Suppress inline result or report only as unverified
        end
        Verify-->>UI: Explicit completed/failed/skipped checks and partial-review state
    end

    UI-->>Dev: Read-only summary; no finding means only “not detected”
    Dev->>Feedback: Label finding (accepted, rejected, duplicate, not actionable, fixed, or uncertain)
    Feedback->>Feedback: Store as product feedback, linked to run and snapshot
    Note over Feedback,Audit: Feedback is not benchmark truth and never silently changes gold labels.
    Feedback-->>Dev: Acknowledge recorded feedback
    opt Separate benchmark adjudication, under its own blinded protocol
        Audit->>Feedback: Review de-identified candidate/feedback evidence
        Audit-->>Audit: Versioned adjudication decision and audit trail
    end
    Note over Dev,UI: No automatic approval, merge, repository write, or fix execution is part of this journey.
```

## Acceptance conditions

| Journey stage | Required observable behavior |
|---|---|
| PR event | Authenticate the provider event, apply least privilege, and deduplicate retries before starting work. |
| Snapshot | Bind every run to immutable base/head commit identities and a stable snapshot identifier; never silently substitute a newer PR revision. |
| Review | Treat repository files, comments, tool output, and model output as untrusted data. Report unavailable, failed, skipped, timed-out, truncated, or unsupported checks explicitly. |
| Finding verification | Validate finding structure, evidence, policy, duplicate status, and changed-line anchors against the exact reviewed snapshot. An invalid anchor is not posted inline. |
| Presentation | Keep the flow read-only. Show uncertainty and partial completion. A lack of findings is not a pass or proof of safety. |
| Developer feedback | Preserve feedback as feedback tied to a run/snapshot. It does not directly mutate gold labels or benchmark scores. Any benchmark adjudication is separate, versioned, and blinded as required by its protocol. |
| PR changes during a run | A newer head creates a distinct snapshot/run; output for an older head is marked stale or superseded and must not be represented as review of the new head. |

## Acceptance evidence

This sequence diagram covers the required path `PR open → snapshot → review → verified findings → developer feedback`, including explicit partial/unavailable outcomes and the boundary between product feedback and benchmark adjudication. It is a design artifact only; it does not demonstrate that any of these integrations or behaviors currently execute.
