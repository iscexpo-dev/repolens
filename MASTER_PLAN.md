# Best AI Code Reviewer 2026 — Master Build Plan

**Project type:** Production AI engineering platform + reproducible benchmark suite  
**Snapshot:** 24 October 2026  
**Document status:** Proposed design and validation plan; no implementation or benchmark result is being claimed as completed.  
**Mission:** Build an all-in-one AI code reviewer that catches actionable real-world defects, explains them with evidence, proposes safe fixes, verifies those fixes, and publishes honest comparisons backed by repeatable evaluation.

---

## 1. Executive summary

Build a repository-aware review system around a **hybrid of language models, deterministic analyzers, test execution, and a strict finding-verification layer**. The product must not equate more comments with better review quality. Its north-star outcome is the number of meaningful defects prevented per unit of developer attention and cost.

The project has two connected deliverables:

1. **Review platform:** Integrations, repository context, risk-adaptive analysis, structured findings, optional patch generation, test-backed verification, security controls, and a feedback loop.
2. **Benchmark platform:** Versioned datasets, fixed evaluation protocols, independent comparison of commercial and open tools/models, false-positive measurement, confidence intervals, and public scorecards that distinguish measured results from vendor claims.

The first release should focus on GitHub pull requests and a limited but well-supported set of languages. Extend integrations and language coverage only after the end-to-end benchmark proves that the core review experience is useful. Do not begin by training a foundation model from scratch: first establish a reproducible baseline and improve the review agent, context selection, verification, and routing around strong available models.

### Non-negotiable principle

> **Optimize for verified defects prevented, not comments generated.**

“Unlock all limitations” is not a verifiable engineering promise. No reviewer can guarantee discovery of every defect. The attainable goal is to measure known blind spots, expand coverage deliberately, disclose uncertainty, and demonstrate improvements on held-out real-world pull requests.

---

## 2. Product outcomes and scope

### 2.1 Primary users

- Individual developers who want high-signal reviews before asking teammates for approval.
- Engineering teams working in multi-package repositories, service-oriented backends, or legacy systems.
- Security engineers who need an additional review layer alongside established scanners.
- Platform and DevEx teams who need consistent review policies across repositories.
- Researchers and engineering leaders who need reproducible comparisons among review tools and model configurations.

### 2.2 Product experience

For every pull request, the reviewer should:

1. Explain what changed and identify high-risk portions.
2. Find likely correctness, reliability, security, performance, testing, and maintainability issues.
3. Anchor every finding to a valid changed line when an inline comment is appropriate.
4. Explain the triggering conditions, impact, evidence, and why the issue is not merely stylistic preference.
5. Offer a minimal proposed fix when it can be justified.
6. Run suitable checks on proposed fixes in an isolated environment.
7. Clearly report what was checked, what could not be checked, and the remaining uncertainty.
8. Learn from developer feedback without silently treating every dismissal or acceptance as ground truth.

### 2.3 Scope by release

**MVP**
- GitHub App/webhook integration, pull-request snapshots, diff parsing, repository context retrieval.
- One provider-neutral model interface with at least two model configurations for controlled comparisons.
- Deterministic tool integrations: existing tests, lint, type checking, and selected SAST/SCA tools.
- Structured findings, deduplication, risk/severity ranking, PR summary, review dashboard.
- Offline benchmark runner, repeatable scorecards, cost/latency tracking.
- Read-only-by-default permissions and safe failure behavior.

**Post-MVP**
- Isolated patch generation with tests and re-scan.
- GitLab integration, then Bitbucket/Azure DevOps based on demand.
- Organization-specific review rules, private benchmark sets, policy controls, and audit exports.
- More languages and language-specific analyzers.
- Opt-in IDE/CLI workflows and self-hosted deployment.

**Explicit non-goals for the first release**
- Claiming 100% bug detection or guaranteeing secure/correct code.
- Automatically merging code or independently approving a pull request.
- Running arbitrary repository scripts with production credentials or unrestricted network access.
- Ranking products from vendor marketing claims alone.
- Treating generated comments, stars, or raw issue counts as a measure of review quality.

---

## 3. Current evidence and competitive baseline (as of 24 October 2026)

Different benchmarks answer different questions. Results should not be mixed into one universal leaderboard without normalization and clear caveats.

| Evidence source | Publicly reported setup | What it contributes | Main caveat |
|---|---|---|---|
| [GitHub ReviewBench](https://github.com/review-bench/ReviewBench) | 219 public PRs across 187 repositories and 19 languages; a separate 25-task test set | Open, reproducible comparison using a multi-source finding set; grounded and augmented metrics; severity/category slices | Still a finite public corpus. Keep a hidden holdout to reduce benchmark overfitting. |
| [CRBugBench / Microsoft Research](https://www.microsoft.com/en-us/research/publication/when-should-a-software-factory-be-lights-off-benchmarking-code-review-agents-on-bug-detection/?lang=ja) | 1,000 tasks from 98 open-source repositories plus 800 tasks from proprietary industry repositories | Tests bug detection on changes known to have introduced human-verified bugs; highlights context-sensitive and complex cases | Proprietary data is not fully reproducible by outside teams; its result applies to the authors' evaluated configuration. |
| [SWE-PRBench](https://arxiv.org/abs/2603.26130) | 350 PRs; human-annotated review issues; several frozen context configurations | Separates review quality from code-generation success and studies context effects | Reported results are tied to the tested models, prompts, dataset, and rubric. |
| [CodeReviewBench](https://www.codereviewbench.com/) | 30 merged PRs, 95 confirmed bugs, one shared review harness | Useful small, auditable baseline with precision, recall, cost, and uncertainty indicators | Small sample and limited harness coverage; near-ties should not be overinterpreted. |
| [OWASP Secure Coding with AI](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) | Practical security guidance for agentic coding workflows | Threat model for indirect prompt injection, untrusted repository content, excessive permissions, and unsafe execution | Security guidance, not a code-review accuracy benchmark. |

### Interpretation for our design

- A recent Microsoft Research result reports that its strongest evaluated configuration found 71.9% of bugs within its top five comments, while performance was weaker on complex/non-local issues and proprietary repositories. This is evidence of progress, not proof that autonomous review is safe.
- SWE-PRBench reports that tested frontier models found only 15–31% of human-flagged issues in its diff-only configuration. Its experiments also show that more context is not automatically better; unselective context can dilute attention.
- ReviewBench's grounded metrics support strict apples-to-apples comparison, while augmented metrics help assess legitimate new issues outside the existing gold set.
- CodeReviewBench explicitly notes that its sample is small and confidence intervals often overlap. That is the correct standard for communicating uncertainty.

**Decision:** Use ReviewBench, SWE-PRBench, and other legally usable public datasets as external baselines. Build a separate, versioned internal benchmark with clean PR controls, verified bugs, cross-file and domain-specific issues, and a protected holdout. Do not claim to have reproduced a published result until our exact run artifacts and configuration are available.

### 3.1 Tool baseline shortlist

The existing comparison identifies the following products as candidate baselines. This is a shortlist by role, **not an independently measured ranking**.

| Candidate | Evaluation role | What to measure |
|---|---|---|
| CodeRabbit | General-purpose hosted PR review | Finding precision/recall, comment usefulness, latency, cost, integrations |
| GitHub Copilot Code Review | Native GitHub review and fix delegation | Review quality within native workflow; additional tooling and plan requirements |
| Cursor Bugbot | Bug detection and agent-driven remediation | Defect detection, successful safe fixes, regression rate |
| Qodo | Review rules, team standards, and test workflows | Rule adherence, test usefulness, organization-level consistency |
| Greptile | Repository-wide and cross-file understanding | Non-local bug detection and context quality |
| Bito | Developer workflow and codebase-aware feedback | Cost-quality ratio, adoption, false-positive burden |
| GitLab Duo Code Review | Native GitLab merge-request workflow | GitLab integration quality and coverage |
| SonarQube Cloud | Deterministic quality analysis and gates | Rule-based issue recall, precision, gate stability, remediation verification |
| Semgrep | Security analysis and remediation | Vulnerability recall, false-positive rates, fix correctness |
| PR-Agent | Self-hosted/customizable review workflow | Deployment control, extensibility, maintenance cost, measured review quality |

Compare only against products actually accessible and permitted for testing. Record the exact product version, plan, model, settings, date, repository snapshot, and tool permissions. Product capabilities and prices change; verify current vendor documentation at experiment time.

---

## 4. System architecture

### 4.1 High-level flow

```text
Git provider webhook
        |
        v
Auth + tenant policy + PR snapshotter
        |
        v
Diff parser + change/risk classifier
        |
        +----------------------------+
        |                            |
        v                            v
Repository context index      Deterministic analyzers
(AST/symbols/tests/contracts) (tests, lint, types, SAST/SCA)
        |                            |
        +-------------+--------------+
                      v
           Risk-adaptive review planner
                      |
        +-------------+---------------+
        |             |               |
        v             v               v
  Correctness     Security      Reliability/perf/
  reviewer        reviewer      tests/architecture
        |             |               |
        +-------------+---------------+
                      v
       Finding normalization + deduplication
                      |
                      v
           Independent verification
  (evidence check, line anchor, tool/test support,
        severity, confidence, contradiction check)
                      |
                      v
         Policy gate + reviewer output
                      |
          +-----------+-----------+
          |                       |
          v                       v
  PR review comments        Dashboard/audit trail
          |
          v
Optional isolated patch agent -> tests/re-scan -> proposed patch

All stages emit versioned evaluation and observability events.
```

### 4.2 Recommended first implementation stack

Choose a modular architecture rather than starting with many independently deployed microservices.

- **API/orchestration:** Python + FastAPI, typed request/response schemas, background job queue.
- **Web UI:** Next.js + TypeScript.
- **Persistence:** PostgreSQL for organizations, repositories, PR snapshots, findings, policies, and evaluation runs; object storage for larger snapshots and artifacts.
- **Queue/cache:** Redis or an equivalent queue/cache service, with idempotency and retry controls.
- **Code understanding:** Tree-sitter for broad syntax coverage, supplemented by language-native parsers, language servers, build graphs, import/call relationships, and test mapping where available.
- **Static analysis:** Integrate the tools already used by the repository. Candidate integrations include Semgrep/CodeQL, linters, type checkers, dependency scanners, and secret scanners. Treat each tool's findings as evidence with provenance, not as infallible truth.
- **Execution sandbox:** Ephemeral isolated workers with strict CPU/memory/time quotas, non-root processes, filesystem isolation, restricted syscalls, and no secrets. Use a stronger isolation boundary for untrusted code than a normal application container alone where the threat model requires it.
- **LLM layer:** Provider-neutral adapter interface, configurable model routing, structured output validation, deadlines, retries, rate limits, usage accounting, and optional self-hosted inference.
- **Observability:** Traces and event logs linking each finding to the PR snapshot, prompt/config version, model/provider, tool calls, costs, latency, verification, and eventual developer feedback. Redact source and secrets from operational logs.

These are proposed choices, not requirements to commit every component on day one. Keep interfaces stable so the queue, storage, model provider, and sandbox can change without redesigning review logic.

### 4.3 Repository context engine

Do not copy the entire repository into every model context. Build a relevance-ranked context pack for each change.

**Context sources, prioritized by relevance:**
1. Changed lines and surrounding syntax-aware blocks.
2. Full changed functions/classes and their direct callers/callees.
3. Related interfaces, types, data models, API schemas, database migrations, and configuration.
4. Relevant tests, fixtures, test helpers, and build/test commands.
5. Related code paths identified through symbols/imports/call graph and previous verified incidents where allowed.
6. Repository review rules, code ownership, and architecture constraints after checking that instruction files are trusted and reviewed.

Every retrieved item should carry a path, line range, commit hash, retrieval reason, and provenance. Context must be token-budgeted and de-duplicated. Use separate packs for separate review hypotheses when useful. Evaluate context selection with ablation tests: diff only, diff + nearby code, diff + selected graph, and broader context. Keep the configuration that improves held-out quality, not the one that sends the most context.

### 4.4 Risk-adaptive model routing

Use a provider-neutral router rather than hard-coding one vendor as universally best.

Inputs to routing:
- Diff size, change shape, changed file types, language, and test status.
- Security-sensitive paths such as authentication, authorization, cryptography, payments, or secrets.
- Cross-service/schema changes and estimated number of affected symbols.
- Repository size, language support confidence, and latency/cost budget.
- Historical evaluation for that issue category and repository policy.

Possible stages:
1. Cheap triage to classify change type and prioritize risks.
2. Fast deterministic checks for every PR.
3. Standard review model for common changes.
4. Stronger reasoning or specialist pass for high-risk/cross-file changes.
5. Independent critic/verifier pass only for important candidate findings or ambiguous decisions.
6. Final deduplication/ranking pass.

Ensembling is justified only if the incremental detection gain is worth its latency, cost, and false-positive burden. Multiple models may share the same blind spots; agreement alone is not proof. Route using measured per-category performance and keep a record of the router version.

---

## 5. Finding contract and review quality

### 5.1 Structured finding schema

Each finding should be a typed object before it becomes a comment. A minimal contract:

```json
{
  "finding_id": "stable-id",
  "category": "correctness|security|reliability|performance|testing|maintainability|other",
  "severity": "critical|high|medium|low|informational",
  "title": "Short, specific defect description",
  "path": "relative/path/to/file",
  "start_line": 42,
  "end_line": 45,
  "trigger": "Conditions required for the defect to occur",
  "impact": "Concrete consequence and affected behavior",
  "evidence": [
    {"path": "relative/path/to/file", "start_line": 42, "end_line": 45, "reason": "Evidence relevant to the claim"}
  ],
  "confidence": 0.0,
  "suggested_fix": "Optional minimal fix or patch reference",
  "verification": {
    "tests_run": [],
    "static_findings": [],
    "reproduced": false,
    "limitations": []
  },
  "provenance": {
    "review_config": "versioned-config-id",
    "model_route": "versioned-route-id",
    "tools": []
  }
}
```

The confidence field must not be exposed as a calibrated probability until calibration has been measured. Validate finding schemas, line anchors, duplicate identity, and allowed severity/category values before posting any result.

### 5.2 What counts as a valuable finding

A finding must be:
- **True:** supported by the changed code and relevant repository behavior.
- **Actionable:** the author can identify what to change or investigate.
- **Material:** not merely stylistic preference or a trivial hypothetical.
- **Localized:** tied to a changed line or a clearly identified change when inline location is appropriate.
- **Non-duplicative:** not a second comment that repeats the same underlying defect.
- **Scoped:** impact and confidence must not exceed available evidence.

Never invent a failing test, API, data flow, exploit path, benchmark result, or project rule. If evidence is insufficient, suppress the finding or label the uncertainty explicitly. Don't post a finding only because a model can write a plausible explanation.

### 5.3 Review categories

1. Functional correctness, state transitions, and business logic.
2. Boundary conditions, nullability, overflow, encoding, and data validation.
3. Authorization, authentication, tenant isolation, injection, deserialization, cryptography, and data exposure.
4. Reliability, retries, idempotency, timeout handling, error paths, and resource cleanup.
5. Concurrency, races, deadlocks, transaction consistency, and distributed-systems behavior.
6. API/schema compatibility, database changes, migrations, serialization, and contracts.
7. Performance, complexity, memory, I/O, caching, and scalability.
8. Test adequacy, regression risks, brittle assertions, and missing negative cases.
9. Dependency, license, configuration, secrets, CI/CD, infrastructure, and supply-chain risks.
10. Maintainability and architecture only when the concern has material impact and clear evidence.

Style-only feedback should be delegated to configured linters/formatters wherever possible. That preserves reviewer attention for issues that need reasoning.

---

## 6. Safe fix generation and verification

The fix feature is a separate subsystem from detection. A model that detects a bug correctly may still produce an incorrect patch.

### Required workflow

1. Save immutable base/head commit IDs and the original diff.
2. Generate a minimal patch in a disposable worktree or equivalent isolated workspace.
3. Validate that the patch touches only permitted files and does not modify security policies, CI permissions, or unrelated code without an explicit reason.
4. Run targeted unit tests and then required lint/type/security checks.
5. Run broader tests when the change or available budget justifies it.
6. Compare the result against the base: confirm that the suspected issue is addressed and no new failure was introduced.
7. Re-run the review/verification stage on the patch and record every check, skipped check, and failure.
8. Return a suggested patch or draft commit for human review. Never auto-merge in the MVP.

### Fix metrics

- Patch acceptance rate by severity/category.
- Patch application success rate.
- Targeted test pass rate.
- Full validation pass rate.
- Regression rate on held-out tests and re-review.
- Mean number of patch iterations and cost per verified fix.
- Percentage of fixes that pass tests but fail human review.

A passing test suite is useful evidence but not a proof of correctness, especially when coverage is weak. The UI must distinguish “tests passed” from “bug fixed with high confidence.”

---

## 7. Honest benchmark and comparison program

### 7.1 Benchmark suite design

Use three layers:

**Layer A — External reproducibility**
- Run the permitted public ReviewBench and SWE-PRBench configurations unchanged.
- Record commit hash, dataset version, model/provider/model ID, prompts, tools, context policy, sampling settings, judge version, and exact evaluation command.
- Preserve raw outputs and scoring artifacts. Don't silently remove failed or inconvenient runs.

**Layer B — Internal high-fidelity suite**
- Start with a stratified 500-PR pilot and grow toward 1,000+ PRs as annotation and review capacity allow.
- Include multiple repositories, maintainers, team sizes, programming languages, PR sizes, and change shapes.
- Include bug-introducing PRs identified from later fixes, verified security cases, cross-file issues, migrations, API changes, concurrency/reliability issues, and ordinary feature work.
- Include clean/no-action-needed PRs and safe refactors to measure noise, not only buggy PRs.
- Keep repository- and time-separated train/dev/test partitions to reduce leakage. Avoid putting near-identical patches or PRs from the same defect cluster across splits.
- Annotate severity, category, evidence, required context, affected behavior, and whether a finding is actionable.

**Layer C — Private design-partner evaluation**
- Evaluate on opt-in customer repositories under written data and retention terms.
- Use a local runner for sensitive repositories where practical.
- Do not mix private results into public rankings without permission and clear methodology.
- Report the size and selection bias of this sample; one company's repositories do not represent the industry.

### 7.2 Ground-truth construction

No single human, model, or scanner finds every issue. Build a candidate pool from multiple sources:
- Human review comments and expert-created findings.
- Subsequent fixes/reverts and regression history.
- Deterministic static-analysis tools.
- Independently configured review agents from distinct model families.
- Reproducer tests or minimal failing cases when possible.

Then:
1. Semantically deduplicate candidate findings.
2. Remove unsupported, stylistic, duplicate, or non-actionable candidates.
3. Have qualified reviewers label findings without seeing which system proposed them.
4. Use two annotators for a portion or all high-severity cases; send disagreements to adjudication.
5. Measure agreement and publish the rubric, sampling method, data provenance, and known biases.
6. Keep a sealed test set and rotate some new real-world cases into the evaluation set after the release is frozen.

LLM judges may help scale semantic matching, but must be calibrated against blind human adjudication. They must not be the sole source of ground truth. Audit a representative sample of true positives, false positives, unmatched predictions, and disagreements.

### 7.3 Metrics that must be published

| Metric | Why it matters |
|---|---|
| Grounded precision/recall/F1 | Strict comparison with known validated issues |
| Augmented precision/recall/F1 | Separately judges valid findings outside the original gold set |
| High/critical recall | Measures detection of the most consequential known defects |
| Precision by severity/category/language | Reveals where a model is useful or noisy |
| False-positive comments per clean PR | Captures review noise and the cost imposed on developers |
| Top-k recall (e.g., top 3 and top 5 findings) | Measures whether important issues appear before low-value commentary |
| Localization accuracy | Checks whether comments point to the actual changed lines/behavior |
| Evidence validity rate | Checks whether cited code/test evidence supports the claim |
| Reproduction/verification rate | Measures whether a finding can be substantiated through checks when possible |
| Patch correctness and regression rate | Evaluates remediation independently from detection |
| Latency p50/p95 and timeout rate | Measures workflow viability |
| Cost per PR and cost per confirmed true positive | Supports transparent economic comparisons |
| Run-to-run variance | Exposes stochastic instability |
| Developer acceptance and dismissal reasons | Helps assess utility, but is not treated as ground truth automatically |

Report precision-recall curves or multiple operating points instead of choosing one threshold that hides trade-offs. Use repository-level or defect-cluster-aware bootstrap confidence intervals when appropriate. Publish sample counts and confidence intervals beside rankings. If uncertainty intervals overlap, call results statistically inconclusive or tied rather than declaring an artificial winner.

### 7.4 Comparison protocol

For an apples-to-apples test:
1. Freeze the same PR snapshots and repository state for every candidate.
2. Give candidates the same permitted context and tool-access policy when comparing models within the same harness.
3. When comparing actual products, test each product as shipped and report that these include different product features, context, and provider defaults.
4. Record exact model/version, date, plan, config, prompt, timeout, retries, and any unavailable feature.
5. Run repeated evaluations for stochastic systems where budget permits; report variance.
6. Use a common finding-matching rubric and blinded adjudication.
7. Report both product-level comparisons and controlled model/harness comparisons. Do not conflate them.
8. Maintain a separate sealed holdout; do not tune prompts directly against public test labels and then call the result unbiased.
9. Retain raw prediction JSON, logs with secrets redacted, scorecards, and reproducible commands.
10. Publish failures and negative results, including cases where a cheaper baseline performs as well as a complex ensemble.

### 7.5 Proposed scorecard format

Every result row should include:

- System/product and version.
- Model(s), review agent/harness, and relevant tool integrations.
- Dataset revision and run ID.
- PR count, repository count, language distribution, and number of gold findings.
- Precision, recall, F1, high/critical recall, false positives per clean PR, and top-5 recall.
- 95% confidence intervals and repeated-run variance where measured.
- p50/p95 latency, cost/PR, and cost/confirmed true positive.
- Security/privacy settings and whether the model receives repository content externally.
- Known limitations, missing integrations, and whether results are vendor-reported, independently reproduced, or internal-only.

Use a status label for every reported claim: **independently reproduced**, **internal measurement**, **vendor-reported**, or **not measured**.

---

## 8. Threat model and guardrails

Repository contents are untrusted input. A PR can intentionally include prompt-injection instructions in comments, documentation, tests, filenames, dependency metadata, build output, or logs. Do not rely on a model to reliably recognize every attack; reduce the damage possible if it is fooled.

### Mandatory controls

- Install integrations with minimum permissions. The review path should be read-only by default; patch creation gets a separate, scoped permission flow.
- Never expose organization secrets, production credentials, deployment keys, or general-purpose tokens to review agents or test jobs.
- Treat PR titles, descriptions, comments, files, generated output, dependency docs, and repository instruction files as untrusted data. Separate policy instructions from quoted repository content.
- Run builds and tests in disposable sandboxes with least privilege, CPU/memory/time quotas, and restricted filesystem/network access. Use egress allowlists or no network by default.
- Never run arbitrary scripts on the API server or shared control plane.
- Prevent a model from modifying CI policy, permissions, branch protection, or its own trust settings without explicit human approval.
- Verify path/line anchors and patch boundaries server-side; do not trust model-supplied file paths.
- Redact secrets from model input and all logs where feasible; provide retention controls, encryption at rest/in transit, tenant isolation, and explicit data-use policy.
- Add abuse tests for prompt injection, secret exfiltration attempts, malicious dependency install scripts, path traversal, symlink escape, fork PRs, huge diffs, and denial-of-service inputs.
- Keep signed/auditable records of tool permissions, model route, patch artifacts, review decisions, and policy overrides.
- Fail closed for write actions when verification or authorization is uncertain. Never allow unverified model output to merge code automatically.

Security evaluation is a separate release gate, not an optional score category. Follow the relevant [OWASP Secure Coding with AI guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) and update the threat model as agent capabilities change.

---

## 9. Coverage strategy: expand without pretending coverage is complete

### Language coverage tiers

**Tier 1 (MVP):** choose a manageable set with strong parser/tool support and representative demand—for example TypeScript/JavaScript, Python, Go, Java, and Rust. Confirm the final selection against the target repositories before committing.

**Tier 2:** add languages through tree-sitter, language-specific lint/type/test adapters, and benchmark cases, prioritizing measured demand.

**Tier 3:** lower-support or domain-specific languages, build systems, infrastructure-as-code, SQL-heavy repositories, and embedded/mobile ecosystems; label capability gaps explicitly until benchmarked.

A parser can understand syntax without understanding program behavior. Measure review quality per language and repository type. Do not claim a language is “supported” merely because its files can be tokenized.

### Repository-context coverage

Build dedicated checks for:
- Cross-file contracts and callers/callees.
- API/schema and database migration compatibility.
- Authn/authz and tenant boundaries.
- Asynchronous code, races, retries, and transactional guarantees.
- Infrastructure, CI, deployment, dependency, and secret changes.
- Tests/fixtures and data/serialization changes.
- Monorepos with multiple packages, services, and build/test commands.

For each category, maintain examples of known successes, known failures, and “not enough evidence” cases. Track missed issues by root cause and route those gaps to roadmap items.

---

## 10. Delivery roadmap

A focused MVP is plausibly a 12–14 week effort for a small senior team, depending on integration requirements, data annotation capacity, and production constraints. This is a planning estimate, not a delivery guarantee.

### Phase 0 — Charter and benchmark protocol (Week 1)
- [ ] Agree on target user, deployment/privacy requirements, and initial languages.
- [ ] Freeze definitions for actionable finding, severity, categories, and false positive.
- [ ] Review dataset licenses, terms, and permitted uses.
- [ ] Create a model/product evaluation matrix and preregister the first comparison protocol.
- [ ] Define baseline metrics, data retention, and security boundaries.

**Exit gate:** A versioned spec and benchmark protocol are approved before results are collected.

### Phase 1 — Ingestion and snapshots (Weeks 2–3)
- [ ] Create GitHub App, webhook validation, idempotency, retries, and rate-limit handling.
- [ ] Persist immutable base/head identifiers and safely retrieve diffs/files.
- [ ] Build parser for diff hunks, changed-line mapping, rename/deletion handling, and large-diff policy.
- [ ] Define normalized PR, file, finding, tool, and run schemas.
- [ ] Add tenant isolation, audit events, and minimum permissions.

**Exit gate:** Replay the same PR snapshot deterministically and prove webhook retries do not duplicate reviews.

### Phase 2 — Baseline reviewer and benchmark runner (Weeks 4–5)
- [ ] Add provider adapters and a simple, versioned review prompt/config.
- [ ] Implement structured output validation and finding de-duplication.
- [ ] Integrate the external benchmark runner and a first set of internal PRs.
- [ ] Store raw outputs, cost, latency, model configuration, and scorecards.
- [ ] Evaluate at least two model configurations under the same harness.

**Exit gate:** Reproducible end-to-end offline evaluation; every reported result is traceable to a run ID.

### Phase 3 — Context and deterministic analyzers (Weeks 6–7)
- [ ] Add syntax-aware context selection, import/symbol relationships, tests, and config/schema retrieval.
- [ ] Connect repository-native lint, type, test, SAST, and dependency checks.
- [ ] Add risk classification and targeted test selection.
- [ ] Run ablation experiments for diff-only, local context, and selected cross-file context.
- [ ] Track regressions by issue category and language.

**Exit gate:** Context/tool additions improve held-out utility or are disabled; no assumption that more context is automatically better.

### Phase 4 — Verification and signal calibration (Weeks 8–9)
- [ ] Add evidence consistency checks, line-anchor validation, contradiction checks, and issue grouping.
- [ ] Add independent verification for high-risk candidate findings.
- [ ] Calibrate confidence against blinded human labels.
- [ ] Implement false-positive suppression and configurable review policies.
- [ ] Add clean PRs and adversarial cases to the test suite.

**Exit gate:** The team can explain the precision/recall/noise trade-off and identify unsupported findings before release.

### Phase 5 — Remediation sandbox (Weeks 10–11)
- [ ] Build isolated patch generation and worktree lifecycle.
- [ ] Enforce allowed paths, command policy, resource limits, and network controls.
- [ ] Run targeted tests, lint/typecheck, and relevant security re-scans.
- [ ] Produce a patch report with passed, failed, skipped, and unavailable checks.
- [ ] Ensure all write actions require explicit authorization.

**Exit gate:** Patch artifacts are isolated, auditable, reproducible, and never merge automatically.

### Phase 6 — Pilot, security review, and release (Weeks 12–14)
- [ ] Run a blind internal evaluation across supported languages and repository types.
- [ ] Red-team prompt injection, secret handling, malicious scripts, and fork-PR behavior.
- [ ] Run an opt-in pilot with design partners and capture false-positive reasons.
- [ ] Compare offline metrics with human usefulness and production review outcomes.
- [ ] Publish limitations, evaluation protocol, and reproducible scorecards.
- [ ] Add rollback/kill-switches, budgets, alerts, backup/restore, and incident response.

**Exit gate:** Meet predefined quality, security, operational, and privacy gates; otherwise remain in pilot.

---

## 11. Proposed release gates (targets, not measured achievements)

These are initial engineering targets to validate with the first benchmark pilot. They are not claims about the current prototype.

| Area | Proposed gate | Action on failure |
|---|---|---|
| Evaluation integrity | Every score has run ID, dataset version, config, raw output, and scoring artifacts | Block publication |
| High-severity usefulness | Meet a preregistered precision/recall target on a blind, adjudicated set; establish the numeric target after the pilot baseline | Keep in internal pilot and re-tune |
| Review noise | Report false-positive comments per clean PR and set an explicit maximum acceptable rate with design partners | Tighten threshold/suppress low-value categories |
| Security | No secrets available to review/test agents; no unauthorized writes; adversarial injection suite passes agreed gates | Block release |
| Fix safety | No auto-merge; every patch runs in isolation and reports incomplete checks | Disable remediation feature if unsafe |
| Reliability | Idempotent events, bounded retries, job timeouts, and clear partial-failure reporting | Block production rollout |
| Performance | Publish p50/p95 latency and cost for PR size bands; set service objectives from pilot data | Route by risk/budget or reduce scope |
| Honest claims | Separate vendor claims, internal measurements, and independent reproductions | Correct or retract scorecard |
| Regression control | New model/prompt/router versions must be evaluated on sealed tests before rollout | Roll back to last approved config |

**Recommendation:** Do not set a high-looking metric target before measuring a baseline. Establish the baseline first, select operating points based on review-noise tolerance and severity, preregister the target, and keep a hidden holdout for the release decision.

---

## 12. Repository structure proposal

```text
best-ai-code-reviewer/
├── apps/
│   └── web/                    # Next.js dashboard and review history
├── services/
│   ├── api/                    # Auth, tenants, webhooks, policies
│   ├── orchestration/          # Review DAG, retries, router, budgets
│   ├── context-engine/         # Retrieval, AST/symbol index, context packs
│   ├── review-worker/          # Model calls and finding normalization
│   ├── verification-worker/    # Deterministic tool integration and checks
│   └── sandbox-worker/         # Isolated test/fix jobs
├── packages/
│   ├── schemas/                # Typed schemas and API contracts
│   ├── review-core/            # Finding rules, dedupe, severity, policies
│   ├── model-adapters/         # Provider-neutral interfaces
│   ├── git-providers/          # GitHub now; GitLab later
│   └── observability/          # Tracing, metrics, redaction
├── integrations/
│   ├── github-app/
│   ├── gitlab/
│   └── analyzers/              # SAST/SCA, linters, typecheck adapters
├── benchmark/
│   ├── datasets/               # Metadata/manifests; respect licenses
│   ├── runner/                 # Frozen snapshots and controlled execution
│   ├── scoring/                # Matching, metrics, confidence intervals
│   ├── adjudication/           # Human annotation rubric and QA
│   └── reports/                # Generated, versioned scorecards
├── evals/
│   ├── regression/
│   ├── security/
│   ├── context-ablation/
│   ├── routing/
│   └── patches/
├── infra/
│   ├── dev/
│   ├── production/
│   └── sandbox/
├── docs/
│   ├── PROJECT_CHARTER.md
│   ├── ARCHITECTURE.md
│   ├── BENCHMARK_PROTOCOL.md
│   ├── SECURITY_THREAT_MODEL.md
│   └── RUNBOOK.md
└── README.md
```

Keep the first release deployable as a modular application with workers. Extract services only when scale, security isolation, or team ownership justifies the additional operational complexity.

---

## 13. Core implementation tickets

### P0 — Foundation
- [ ] Define typed schemas and versioning for PR snapshots, context items, findings, tool results, and evaluation runs.
- [ ] Create local development environment, secret management, CI, unit tests, lint, and typecheck.
- [ ] Implement GitHub webhook signature verification and idempotent job creation.
- [ ] Add immutable PR snapshot storage and reproducible replay.
- [ ] Add model-provider abstraction, cost budgets, and timeouts.

### P1 — Reviewer baseline
- [ ] Implement diff-aware review with structured output.
- [ ] Validate changed-line anchors and repository paths.
- [ ] Deduplicate findings and enforce comment budget.
- [ ] Build finding display and a PR summary.
- [ ] Record all model calls and configurations for offline replay.

### P2 — Context and tools
- [ ] Implement language-aware context packs and token budgets.
- [ ] Add selected caller/callee, schema, configuration, and test retrieval.
- [ ] Add analyzer adapters and normalized tool findings.
- [ ] Evaluate routing and context ablations on hidden PRs.

### P3 — Benchmark quality
- [ ] Import approved external benchmark datasets with provenance and licenses.
- [ ] Build semantic matching plus a calibrated judge workflow.
- [ ] Create no-issue PR controls and a double-blind annotation interface.
- [ ] Generate precision/recall/F-score, severity/category slices, and confidence intervals.
- [ ] Add run-to-run variance and cost/latency reports.

### P4 — Safe remediation and production
- [ ] Implement sandboxed patching with strict permissions.
- [ ] Validate tests, lint, types, and relevant security checks after patching.
- [ ] Add human acceptance/dismissal feedback and reason codes.
- [ ] Add tenant privacy controls, retention deletion, operational alerts, and audit export.
- [ ] Complete threat modeling, penetration testing, rollout guardrails, and rollback procedures.

---

## 14. Team and execution model

A practical initial team is 4–6 experienced contributors, with roles that may be combined:

- **Tech lead / review systems:** architecture, integration, reliability, code-review UX.
- **ML/agent engineer:** context selection, model routing, structured prompting, verifier design.
- **Evaluation engineer:** dataset quality, annotation rubric, scoring, statistical reporting, benchmark integrity.
- **Backend/platform engineer:** provider integrations, storage, queues, multi-tenant security, observability.
- **Security engineer/reviewer:** threat model, adversarial tests, sandbox and tool permissions.
- **Frontend/DevEx engineer:** dashboard, PR workflow, developer feedback, adoption measurement.

Operate with short iterations and benchmark-driven review. Each change to prompts, retrieval, tools, routing, or models needs a regression report. Review failures as data: classify root cause, reproduce where possible, add a regression case, then fix the system. Never delete a difficult case because it reduces the score without documenting why the annotation itself was invalid.

---

## 15. Weekly operating dashboard

Track the system itself as a product:

- Quality: grounded precision/recall, augmented precision, high-severity recall, false positives per clean PR, top-5 recall.
- Safety: prompt-injection test pass rate, secret-exposure incidents, unauthorized actions, sandbox violations.
- Remediation: test-pass rate, regression rate, patch acceptance.
- Efficiency: cost per PR, cost per confirmed true positive, p50/p95 latency, timeouts, retries.
- Coverage: supported-language results, issue-category gaps, cross-file bug performance, missing-test/tool coverage.
- User experience: accepted/dismissed comments by reason, time spent per finding, review completion time, usefulness feedback.
- Model lifecycle: results by model/router/prompt revision, benchmark drift, provider errors, rollback count.

Don't optimize a single dashboard number. For example, increased recall is not an improvement if it doubles false positives and makes developers ignore all comments.

---

## 16. Decision checklist before calling it “best”

Do not market the product as “best” until the team can answer yes to these questions with artifacts:

- [ ] Did we compare against relevant commercial and open baselines under a documented protocol?
- [ ] Are the public dataset and product/version details reproducible?
- [ ] Did we measure false positives on clean PRs as well as recall on buggy PRs?
- [ ] Are severe findings separated from low-priority suggestions?
- [ ] Are confidence intervals, sample sizes, missing runs, and limitations visible?
- [ ] Were LLM-judge outputs audited against blinded human judgments?
- [ ] Is the test set separated from prompt/model tuning data?
- [ ] Did we evaluate real-world cross-file and private-codebase behavior where authorized?
- [ ] Are fixes independently tested, with regressions reported?
- [ ] Are repository contents treated as untrusted input and execution isolated?
- [ ] Can a customer control data retention and model/data-processing policy?
- [ ] Do production outcomes support the offline benchmark improvements?

If a point is not measured, label it **not measured**. A trustworthy unknown is better than an invented result.

---

## 17. Immediate next step

Start with **Phase 0 and Phase 1**, not an elaborate multi-agent system. Establish the charter, baseline protocol, first benchmark slice, GitHub ingestion, immutable replay, and a simple reviewer that emits typed findings. Then measure its weaknesses before adding more agents or models.

The first milestone is complete only when a reviewer can replay a fixed PR, produce reproducible output artifacts, and report precision/recall, false-positive burden, latency, and cost using a documented scoring process. That creates the foundation for every later improvement.

---

## References

1. GitHub, “ReviewBench: An open benchmark for AI code review,” 5 October 2026. https://github.blog/ai-and-ml/reviewbench-an-open-benchmark-for-ai-code-review/
2. ReviewBench repository and evaluation harness. https://github.com/review-bench/ReviewBench
3. Microsoft Research, “(When) Should a Software Factory be Lights-off? Benchmarking Code Review Agents on Bug Detection,” October 2026. https://www.microsoft.com/en-us/research/publication/when-should-a-software-factory-be-lights-off-benchmarking-code-review-agents-on-bug-detection/
4. SWE-PRBench, “Benchmarking AI Code Review Quality Against Pull Request Feedback,” March 2026. https://arxiv.org/abs/2603.26130
5. CodeReviewBench, public benchmark and scorecards. https://www.codereviewbench.com/
6. OWASP, “Secure Coding with AI Cheat Sheet.” https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html
7. AI Code Review tools/top-10 comparison supplied with the project request, research snapshot dated 24 October 2026. Product descriptions are treated as a shortlist of candidates, not independent evidence of performance.
