# System Context and Trust Boundaries

**Status:** Proposed architecture, informed by the current scaffold. This document is a design artifact, not evidence that the depicted integrations, infrastructure, or controls are deployed or working.

## 1. System context and intended data flows

The diagram describes the intended read-only-by-default review flow. Boxes marked **planned** are not implemented in this repository. The existing API/parser/scorer code is shown separately in the implementation inventory below.

```mermaid
flowchart LR
    Dev[Developer / repository administrator]
    Git[Git provider<br/>PR events and repository content<br/><b>planned integration</b>]
    UI[Read-only review results and status<br/><b>planned</b>]
    Model[External model provider<br/><b>planned; receives approved minimum context</b>]

    subgraph Platform["Review platform — trusted service plane (proposed)"]
        Ingest[Webhook/API ingress<br/>authenticate event; authorize; deduplicate]
        Orchestrator[Review orchestrator<br/>bind run to snapshot and policy]
        Verify[Finding and evidence verifier<br/>validate output against exact snapshot]
        DB[(Metadata database<br/>runs, policy versions, findings, audit)]
        Objects[(Object storage<br/>immutable snapshot and permitted artifacts)]
        Queue[[Job queue<br/>snapshot/run references]]
    end

    subgraph Workers["Analysis workers — isolated service identities (proposed)"]
        Analyzer[Deterministic analyzer workers<br/>configured static checks only]
        ModelWorker[Model adapter worker<br/>schema validation, timeout, usage controls]
    end

    Sandbox[Ephemeral sandbox worker<br/>untrusted tests/fix commands only<br/>no secrets; restricted network/resources<br/><b>planned, not implemented</b>]

    Dev -->|opens or updates PR| Git
    Git -->|authenticated event| Ingest
    Ingest -->|read-only fetch: repository, base/head IDs, diff| Git
    Ingest -->|snapshot bytes and digest| Objects
    Ingest -->|snapshot/run metadata| DB
    Ingest -->|job reference; no credentials or source payload| Queue
    Queue --> Orchestrator
    Orchestrator -->|load exact snapshot| Objects
    Orchestrator -->|load effective policy/version| DB
    Orchestrator -->|permitted static-analysis input| Analyzer
    Orchestrator -->|minimum permitted diff/context| ModelWorker
    ModelWorker -->|approved prompt data, never provider credentials| Model
    Model -->|untrusted candidate findings| ModelWorker
    Analyzer -->|untrusted tool results and status| Verify
    ModelWorker -->|untrusted structured candidates| Verify
    Orchestrator -.->|optional, explicitly authorized test/fix job| Sandbox
    Sandbox -.->|untrusted result, exit status, bounded artifacts| Verify
    Verify -->|validated findings, evidence, partial/failure state| DB
    Verify -->|result/status reference| UI
    UI -->|read-only results and limitations| Dev
```

### Flow constraints

1. The provider event is authenticated and authorized before a run is created. Fetches are read-only and bind the run to immutable base/head identities; a changed head is a different snapshot/run.
2. Store source snapshots separately from operational metadata. Queue messages carry identifiers, not source contents or credentials. Storage, retention, encryption, and tenant-isolation implementations remain design/implementation work.
3. Repository files, PR descriptions, model responses, analyzer output, and sandbox output are untrusted **data**, never authority to change policy, permissions, or tool access. The verifier checks candidates against the exact snapshot and reports failed, skipped, partial, and unavailable checks explicitly.
4. The model adapter sends only the minimum context permitted by the selected policy and provider configuration. Provider credentials stay in a service-side secret boundary and are not exposed to repository content, the model prompt, or workers that do not need them.
5. The API/orchestrator does not execute repository scripts. Static analyzers must be explicitly configured and bounded; commands that execute repository-controlled code belong only in the separately isolated sandbox. The sandbox is not a general networked worker.
6. The default result path is read-only. Any future write-back to the Git provider requires separate explicit authorization and least-privilege scope; automatic approval or merge is out of scope.
7. “No finding” means only “not detected by checks actually run.” Missing context, failed tools, unsupported inputs, timeout, or sandbox unavailability are unverified/partial outcomes, not passes.

## 2. Trust zones and crossings

```mermaid
flowchart TB
    subgraph Z0["Zone 0 — human and source systems (outside platform control)"]
        User[Developer / administrator]
        Repo[Repository, PR text, commits, files]
        Git[Git provider]
    end

    subgraph Z1["Zone 1 — platform control plane (planned)"]
        API[Authenticated ingress and orchestration]
        Secrets[Least-privilege integration/provider credentials]
        Policy[Validated policy and run identity]
    end

    subgraph Z2["Zone 2 — persistent data plane (planned)"]
        DB[(Tenant-scoped metadata and audit)]
        Store[(Snapshot/artifact object storage)]
        Q[[Queue: identifiers only]]
    end

    subgraph Z3["Zone 3 — analysis service workers (planned)"]
        Static[Deterministic analyzers]
        Adapter[Model adapter]
        Verify[Verifier]
    end

    subgraph Z4["Zone 4 — untrusted-code execution boundary (planned; strongest isolation)"]
        Runner[Ephemeral sandbox<br/>non-root; resource-limited;<br/>restricted egress; no secrets]
        Checkout[Read-only snapshot input<br/>ephemeral writable workspace]
    end

    subgraph Z5["Zone 5 — external model service (provider-specific boundary)"]
        LLM[Configured model provider]
    end

    User -->|PR actions| Git
    Git -->|signed event and read-only content fetch| API
    API -->|narrow credentials; secret access only where needed| Secrets
    API -->|validated snapshot/run metadata| DB
    API -->|snapshot content| Store
    API -->|run reference| Q
    Q -->|reference| Static
    Q -->|reference| Adapter
    Store -->|authorized snapshot reads| Static
    Store -->|minimum permitted context| Adapter
    Adapter -->|untrusted prompt data over provider API| LLM
    LLM -->|untrusted response| Adapter
    Static -->|untrusted findings/status| Verify
    Adapter -->|untrusted candidates| Verify
    Policy -->|scope and limits| API
    Policy -->|run-bound constraints| Static
    Policy -->|run-bound constraints| Adapter
    API -.->|separately authorized execution request only| Runner
    Store -.->|specific immutable input snapshot| Checkout
    Checkout --> Runner
    Runner -.->|untrusted bounded outputs| Verify
    Verify -->|validated result and provenance| DB
    DB -->|read-only result view| User
```

### Boundary rules and current confidence

| Crossing / zone | Required rule | Current status |
|---|---|---|
| Git provider → ingress | Verify provider authentication/signature, installation/repository authorization, payload limits, and replay/idempotency before accepting work. Fetch least privilege. | Requirement/design only; no provider integration is present in the inspected scaffold. |
| Repository content → any service/worker | Treat content as adversarial data. Do not let embedded instructions authorize tools, expose secrets, or change scope. Validate paths, anchors, schemas, and permissions server-side. | Security rules are documented in `docs/SECURITY_BOUNDARIES.md`; comprehensive runtime enforcement is not evidenced. |
| Service → storage/queue | Tenant-scope access; bind records to immutable snapshot/run IDs and policy/config revisions. Queue payloads should contain references, not credentials or source dumps. | Proposed architecture; no database, object storage, or queue implementation is present. |
| Worker → model provider | Use approved minimum context and a service-owned credential; enforce deadlines, output validation, and provider/data-retention policy. Treat model output as untrusted. | No model adapter/provider is present. Provider retention and data-residency decisions remain unresolved. |
| Analyzer → repository code | Static analysis is distinct from executing repository-controlled commands. Do not run repository scripts in the API/orchestrator. | Current source has diff parsing but no analyzer execution integration. |
| Repository code → sandbox | Only an explicitly authorized job may cross. Require ephemeral isolation, resource limits, restricted egress, no developer/production secrets, and bounded artifact return. | Sandbox is not implemented or verified; no untrusted repository code may be run until this boundary exists and passes security tests. |
| Results → developer/Git provider | Validate evidence/anchors and report check status and uncertainty. Default to read-only; no automatic merge. | Current API explicitly says its diff parsing is not a review; no result publishing path is present. |

## 3. What exists versus what is proposed

Observed in source during this task:

- `src/reviewforge/api.py` is a small FastAPI shell with health and changed-line parsing endpoints. Its health response says the review provider is not configured; the parsing endpoint says no review was performed.
- `src/reviewforge/diff.py` parses added lines from unified diffs. It is not a language-aware analyzer or Git integration.
- `src/reviewforge/benchmark/metrics.py` scores supplied, adjudicated finding matches. It does not run a review or perform semantic matching.

The Git provider integration, durable metadata/object storage, queue, orchestration, analyzer/model workers, verifier, user-facing review surface, and sandbox in the diagrams are **planned components, not implemented or deployed components**. The diagrams do not establish their security properties, availability, tenant isolation, or accuracy. `MASTER_PLAN.md` describes PostgreSQL/object storage, a Redis-or-equivalent queue, modular workers, and a future sandbox as proposed options; final technology choices and deployment topology remain open.

## 4. Acceptance coverage and unresolved architecture risks

The two diagrams identify the human/repository actors, Git and model providers, metadata and object storage, queue, analyzer and model workers, sandbox, trust zones, and labeled data flows. This is sufficient evidence for the ARCH-001 documentation acceptance only.

Material unresolved details to settle before implementation include:

- Exact authentication, webhook replay handling, permissions, tenant model, and provider installation lifecycle.
- Selected storage/queue technologies, encryption/key ownership, retention/deletion, backup/restore, and consistency guarantees.
- Whether analysis workers are dedicated per job or shared, and which static analyzers are allowed to process repository content outside the sandbox.
- Sandbox technology and proof of isolation, resource enforcement, restricted egress, secret absence, and artifact sanitation.
- Model-provider retention, data residency, allowed data, and credential isolation.
- Deployment topology and the specific identity/authorization checks at each service boundary.

These are not silently decided by the diagrams. Until the sandbox and service boundaries are implemented and tested, executing untrusted repository code remains prohibited.
