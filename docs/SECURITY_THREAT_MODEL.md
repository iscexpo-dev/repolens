# Security Threat Model — Best AI Code Reviewer

**Status:** Initial design artifact for SEC-001. This is not a security assessment, penetration-test result, control verification, or production-readiness claim. Threats and proposed mitigations describe work required; they are not evidence the controls exist.

**Scope:** Proposed read-only-by-default pull-request review flow described in `REVIEW_USER_JOURNEY.md` and `SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md`, including ingestion, context selection, model/analyzer use, finding verification, persistence, benchmark operation, and a future isolated test/fix worker. This model is bounded to the repository’s current proposal and starter code; deployment topology, provider contracts, and tenant design are not finalized.

## 1. Security objectives

1. Preserve confidentiality and integrity of repository source, credentials, tenant data, review results, and benchmark materials.
2. Restrict access and actions to the authenticated tenant, repository, snapshot, policy, and explicit authorization.
3. Prevent untrusted repository/model/tool content from changing system instructions, permissions, policy, tool selection, or task scope.
4. Never execute repository-controlled code in the API/control plane. Any future execution is isolated, resource-limited, egress-restricted, ephemeral, and has no developer/production secrets.
5. Bind review outputs and evidence to the exact immutable snapshot and disclose unavailable, partial, failed, stale, or unsupported checks.
6. Keep Git interactions read-only by default. No automatic approval or merge.
7. Protect benchmark integrity and distinguish measurement evidence from model/vendor assertions.

## 2. Assets and security impact

| Asset | Security interest / impact if compromised |
|---|---|
| Source code, diffs, PR metadata, commit identities, context packs | Confidentiality, tenant isolation, integrity of exact review scope, retention/deletion obligations |
| Git-provider installation credentials, webhook secrets, model credentials, storage/queue credentials, signing keys | Confidentiality and integrity; misuse may expose source, alter reviews, or grant provider access |
| Tenant, organization, repository, user, and policy identities | Authorization boundaries, correct policy resolution, cross-tenant confidentiality |
| Snapshot manifests, policy/config revisions, run state, findings, tool outcomes, audit records | Integrity, provenance, freshness, non-repudiation/attribution where supported |
| Model prompts/responses and analyzer/sandbox outputs | Confidentiality and integrity; content is untrusted and may contain hostile instructions or fabricated evidence |
| Persistent data, object storage, queue messages, caches, backups, logs, telemetry | Confidentiality, integrity, availability, deletion and tenant isolation |
| Benchmark datasets, protected holdouts, gold labels, raw outputs, score reports | Confidentiality, integrity, reproducibility, resistance to leakage or manipulation |
| Availability, budget, queue capacity, provider quotas, developer attention | Protection from resource exhaustion, runaway cost, false-positive burden, and stale/incomplete results |
| Build/deployment artifacts, dependencies, CI identities, container images and configuration | Supply-chain integrity, credential exposure, and control-plane compromise |

## 3. Actors and trust assumptions

| Actor | Trust treatment |
|---|---|
| Repository contributor, PR author, issue/comment author | Potentially malicious or compromised. All repository and PR content is untrusted data. |
| Git provider and webhook delivery | External dependency. Authenticate events and separately authorize installation/repository access; provider events can be forged, replayed, delayed, duplicated, or refer to changed heads unless validated. |
| Model provider and model output | External processor/dependency. Provider retention/data handling require explicit review. Output is an untrusted candidate, not authority or verified fact. |
| Analyzer, build/test output, package registry | Tool output and dependencies may be malformed, compromised, or instruction-bearing. Do not treat output as trusted instructions. |
| Tenant administrator and repository policy author | Authorized only within explicitly authenticated scope. Misconfiguration or account compromise can weaken controls unless guardrails and audit exist. |
| Platform operator/developer/CI identity | Privileged actor. Least privilege, separation of duties, secret isolation, auditable changes, and incident response are required. |
| Other tenant or external attacker | Not authorized to observe or alter a tenant’s source, jobs, policies, results, or benchmark artifacts. |
| Dependency/build/image maintainer | External supply-chain actor. Versioning, provenance, scanning, and controlled upgrades are needed; package reputation alone is insufficient. |

Assume cryptographic primitives and the underlying host/provider can fail or be misconfigured; threat-model controls must not depend on repository text or model output respecting instructions. Availability of external providers is not guaranteed. No assumption of user intent, model honesty, or successful detection is made.

## 4. Trust boundaries and data flows

The architecture diagram is in `SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md`. Security-relevant crossings are:

1. **Provider → ingress:** signed/authenticated webhook and least-privilege API fetch into the platform.
2. **Untrusted content → service/worker:** source files, PR text, instructions, tool logs, generated artifacts, and model output enter processes that may hold sensitive metadata.
3. **Control plane → persistence/queue:** tenant-scoped records and snapshot references cross service boundaries; queue messages and logs must not become broad source/secret channels.
4. **Model adapter → external model provider:** selected source/context leaves the platform; provider identity, retention, region, and training use matter.
5. **Analyzer/test job → code execution boundary:** static analysis and repository-controlled execution are different risks. Arbitrary code is prohibited in the API; future test/fix commands require a separate sandbox.
6. **Service → Git publication:** read-only result retrieval is distinct from any write-capable PR publishing. Write permission is separately authorized and absent from default review.
7. **Build/deploy pipeline → runtime:** source, dependencies, build artifacts, CI credentials, and deployment configuration can affect all service identities.

Trust-zone names and components in diagrams are design intent only. There is no evidence that the proposed zones, credentials, storage, queue, model boundary, or sandbox currently exist or are isolated.

## 5. Current implemented controls versus proposed controls

### Observed in current source (narrow controls only)

| Observed control | Evidence and limit |
|---|---|
| Diff endpoint requires a non-empty string and sets a maximum request field size. | `src/reviewforge/api.py` uses Pydantic `DiffRequest` with `min_length=1` and `max_length=2_000_000`. This is a field constraint, not complete HTTP/body, authentication, rate-limit, or denial-of-service protection. |
| API response explicitly states that changed-line parsing is not a review and does not assess safety; health indicates provider is not configured. | `src/reviewforge/api.py`. This prevents that endpoint from claiming AI review; it does not secure future integrations. |
| Diff parser rejects non-string input and conservatively invalidates malformed hunk position state. | `src/reviewforge/diff.py`. It is not a complete Git-provider parser or path authorization control. |
| Benchmark scorer rejects duplicate IDs and does not credit nonexistent/cross-PR match IDs. | `src/reviewforge/benchmark/metrics.py`. It assumes supplied match decisions and is not an ingestion or tenant-isolation boundary. |
| Security rules and architecture boundaries are documented. | `docs/SECURITY_BOUNDARIES.md`, `SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md`, and `MODULAR_APPLICATION_BOUNDARIES.md`. These are requirements, not enforcement. |

No Git provider, model provider, persistence/queue, tenant-authentication layer, analyzer execution, finding verifier, publisher, secrets manager, or sandbox was observed. ARCH-002 schemas and tests are draft and unverified; they are not security controls or stable wire contracts. No security tests, sandbox tests, code execution, or independent assessment was performed for this task.

### Proposed controls (not implemented or verified)

- Authenticate and authorize every provider event and repository operation; verify webhook signatures over the original bounded payload, reject invalid signatures, track delivery IDs, handle retries idempotently, and bind fetched content to expected immutable commit identities.
- Enforce tenant identity and repository authorization at every API, database, object-store, queue, cache, search/index, log, and background-job boundary. Use deny-by-default queries and object access; test negative cross-tenant cases.
- Keep credentials in a secret-management boundary; issue short-lived, least-privilege credentials only to the adapter that needs them; never place secrets in prompts, source artifacts, queue messages, or ordinary logs. Rotate/revoke and audit.
- Treat all source, issue/PR text, comments, instruction files, model output, tool output, and sandbox artifacts as tainted data. Keep system policy outside retrieved content; do not execute instructions embedded in content; validate tool requests and permissions in trusted code.
- Send only policy-approved minimum context to an approved model endpoint. Document provider retention, region, training use, deletion, and contractual terms; redact detected secrets before external transmission and presentation.
- Validate schemas, snapshot/run/policy identity, paths, changed-line anchors, evidence provenance, payload sizes, and output limits server-side. Never accept a model-supplied path/anchor or claim a check ran without an observed result.
- Default Git permissions to read-only. Place any future write-capable publisher behind separate explicit authorization, narrow permissions, audit, and human confirmation; do not grant approval or merge capability.
- Do not run repository-controlled scripts in API/orchestration. For the future sandbox, use ephemeral per-job isolation, non-root identity, strict CPU/memory/disk/process/time quotas, no host mounts or credentials, restricted egress and metadata-service blocking, bounded/sanitized outputs, and independent escape testing before any use.
- Pin and inventory dependencies/images; review provenance and licenses; scan for vulnerabilities; protect CI/deployment identities; separate build and runtime credentials; require reviewed changes and artifact integrity; maintain rollback and incident procedures.
- Preserve immutable run/snapshot/policy/config identities and append-only audit provenance where feasible. Protect benchmark holdouts and labels; separate user feedback from gold truth; retain failed and excluded runs.
- Rate-limit and budget-limit ingress, queueing, context, model calls, tool output, and storage. Expose timeout, truncation, unavailable, failed, and partial outcomes; fail closed when authorization/policy/snapshot binding cannot be established.

These controls require threat-driven tests, configuration review, and independent security validation. This list is not itself proof that any mitigation is adequate.

## 6. Threat scenarios, controls, and residual risk

Risk labels below are initial qualitative prioritization, not measured likelihood or a formal risk acceptance. “Current” means only the narrow observed controls in Section 5; “proposed” controls are unimplemented.

| Threat / initial impact | Scenario and trust boundary | Current control evidence | Proposed mitigations | Residual risk / validation needed |
|---|---|---|---|---|
| **Malicious repository content — High** | Crafted files, paths, large/malformed diffs, metadata, generated output, or instructions attempt parser confusion, resource exhaustion, secret access, unauthorized tool use, or misleading findings when crossing into API/workers. | Diff endpoint has field-level length constraints; parser has conservative behavior for some malformed hunks; no auth, full payload controls, tool runner, or verifier was observed. | Enforce request/body/file/token quotas; canonicalize and authorize paths against immutable snapshots; isolate content as data; schema-validate outputs; bound memory/time; keep tools explicitly allowlisted; report partial/truncated scope. | Parser and endpoint edge cases are untested in this session; malformed/large/mixed inputs and downstream components are unverified. Add adversarial fixtures and resource-limit tests before integration. |
| **Prompt injection — High** | Instructions in source, README/agent files, PR descriptions, comments, test logs, or retrieved pages attempt to change system behavior, reveal secrets, invoke tools, or suppress findings. Model output may repeat or amplify the instructions. | Documentation states repository content is untrusted; no model path or prompt/tool enforcement was observed. | Keep instruction hierarchy/policy in trusted code; quote/label retrieved material as data; restrict model capabilities; require trusted deterministic authorization for every tool/action; never let model output call tools directly; test direct/indirect injection, Unicode/control characters, and tool-output instructions. | Prompt-level defenses alone are bypassable. No model adapter or adversarial test suite exists; safety depends on capability isolation and server-side checks that remain unimplemented. |
| **Secret exfiltration — Critical** | Malicious content induces a worker/model to disclose environment variables, credentials, source from another tenant, or deployment data through prompts, outputs, logs, network requests, or artifacts. | No model/provider credentials or secret-bearing review path was observed. Documentation says jobs must not read production credentials; no secret manager, redaction, or egress enforcement was observed. | No secrets in repository-analysis workers; short-lived least-privilege adapter credentials; minimum-context disclosure; secret scanning/redaction; egress allowlists; output/log redaction; key rotation; monitor denied/allowed flows. | Future model transmission inherently discloses selected source to a third party. Provider retention, residency, and terms are unresolved. No controls tested; compromise or false-negative secret scanning remains possible. |
| **Tenant breakout — Critical** | Insecure identifiers, object paths, queue jobs, caches, search, logs, or authorization checks expose or mutate another organization’s source, policy, results, or credentials. | No multi-tenant auth or persistence layer was observed. There are no tenant-isolation tests. | Bind every object and job to authenticated tenant/repository scope; enforce authorization in service and storage adapters; use tenant-scoped keys and isolation; test cross-tenant reads/writes, enumeration, replay, cache collision, and background-job confusion. | Tenant model and storage topology are not selected. Documentation alone provides no isolation; do not onboard multiple tenants until independently tested. |
| **Webhook forgery/replay — High** | An attacker submits a fabricated, altered, duplicated, or replayed event to trigger unauthorized fetches/reviews, consume budget, or target a stale/different head. | No Git integration or webhook endpoint was observed. | Verify signatures on raw bounded body; authenticate installation/repository; reject stale/invalid events; record delivery IDs; idempotently deduplicate; bind accepted work to authorized repository and exact base/head; apply rate limits and replay windows. | No integration tests or credentials exist. Provider lifecycle, retries, rate limits, and stale-run semantics remain unimplemented. |
| **Sandbox escape / unsafe execution — Critical** | Malicious tests/build scripts exploit kernel/runtime/container weaknesses, resource limits, mounted files, network routes, or inherited credentials to reach host, control plane, other jobs, metadata services, or tenants. | No sandbox worker or repository execution path was observed; security docs prohibit API-process execution. This is an absence of capability, not proof of containment. | Do not execute repository code until a separate ephemeral worker is implemented; no host mounts/secrets; non-root; strong process/filesystem isolation; strict quotas; default-deny egress and metadata blocking; per-job identity; sanitized bounded outputs; independent escape and cleanup review. | No sandbox technology chosen or validated. Containerization alone may not be an adequate boundary for the threat model. Any future use remains prohibited until independent security tests pass. |
| **Supply-chain compromise / supply-chain risk — High** | Compromised dependency, transitive package, build action, base image, artifact, or maintainer account introduces malicious code or steals CI/deployment credentials. | `pyproject.toml` declares dependencies/optional extras but no lockfile, provenance policy, SBOM pipeline, or supply-chain validation was observed in the reviewed files. | Lock and review dependency changes; pin/rebuild verified artifacts; record provenance/SBOM; scan dependencies/images; protect CI with least privilege and isolated secrets; require signed/verified releases where feasible; monitor advisories and maintain rollback. | No CI/build provenance or dependency scanning was assessed. Tool availability and repository configuration may be incomplete; independent review and incident process are absent. |
| **Review/result integrity and stale evidence — High** | Findings or results become detached from their snapshot/policy, fabricated by model/tool output, anchored to invalid paths, or published against a newer PR head. | Diff parser calculates added-line positions; API returns parse status only. No immutable snapshot, verifier, or publisher exists. | Bind every result to immutable commit/diff/config/policy identities; verify evidence and anchors server-side; reject stale results; show provenance/check status; keep publication read-only or separately authorized. | No runtime snapshot lifecycle or output path exists. ARCH-002 schemas are unverified; no end-to-end tests establish binding. |
| **Denial of service / cost abuse — High** | Repeated events, huge payloads, expensive context, pathological diffs, provider retries, or tool output exhaust CPU, memory, queue, API quota, or model budget. | API diff field max length is present. No end-to-end request, rate, concurrency, queue, timeout, or spend control was observed. | Per-tenant/global rate and cost limits; bounded parsing/context/output; queue backpressure; deadlines; bounded retries/circuit breakers; concurrency caps; cancel stale jobs; alert on budget exhaustion. | Actual limits and operating envelope are unknown. No load or abuse tests/SLOs were measured. |
| **Benchmark leakage/manipulation — High** | Holdout data, gold labels, matching decisions, or raw outputs are exposed or modified, enabling overfitting or misleading quality claims. | Scorer consumes supplied match IDs and rejects certain invalid/duplicate matches; no dataset access control, immutable run manifest, or holdout enforcement was observed. | Separate protected holdouts; restrict access; version datasets/judges/configs; preserve raw outputs and failures; audit changes; blind-adjudicate novel findings; disclose exclusions and sample size. | No benchmark run or protected dataset exists in this starter. No benchmark-integrity controls are validated. |

## 7. Assumptions, exclusions, and unresolved decisions

- The intended MVP is a read-only Git-provider review path; no automatic merge or approval. Any future patch/test execution is separately authorized and outside current implementation.
- No cloud/provider topology, tenant model, database, queue, object store, secret manager, or sandbox technology is assumed selected by this document.
- Legal/privacy decisions about source transmission, retention, region, provider training use, deletion, and customer controls remain unresolved.
- This initial model does not quantify likelihood, residual risk, service SLOs, attack cost, or control effectiveness. Risk ratings are prioritization labels only.
- Independent security review, penetration testing, provider contract review, privacy assessment, supply-chain assessment, and sandbox escape testing have not occurred.
- Existing security prose, interface contracts, and Python dataclasses are not evidence of implemented enforcement. In particular, no finding or status field can prove its own evidence or verification.

## 8. Validation and status

This document addresses the seven SEC-001 acceptance threats and records scope, assets, actors, trust boundaries, current versus proposed controls, threat scenarios, mitigations, residual risks, and assumptions. Acceptance inspection of the document does not establish implementation, security effectiveness, or readiness for deployment. No repository code or tests were executed; no production-readiness, security-assurance, or benchmark claim is made.

Related artifacts: [`SECURITY_BOUNDARIES.md`](SECURITY_BOUNDARIES.md), [`SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md`](SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md), [`MODULAR_APPLICATION_BOUNDARIES.md`](MODULAR_APPLICATION_BOUNDARIES.md), [`REVIEWER_QUALITY_CONTRACT.md`](REVIEWER_QUALITY_CONTRACT.md), and [`REVIEW_USER_JOURNEY.md`](REVIEW_USER_JOURNEY.md).
