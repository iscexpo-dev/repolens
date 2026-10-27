# Benchmark Protocol — Frozen evaluation rules

**Protocol ID:** `repolens-review-benchmark`
**Version:** `1.0.0`
**Status:** Normative protocol; this is not a dataset, run manifest, or benchmark result.
**Scope:** Offline comparison of code-review configurations on adjudicated pull-request findings.
**Change control:** Any scoring, matching, sampling, label, or eligibility change requires a new protocol version and a dated decision before evaluating candidates. Do not silently rescore a prior run.

## 1. Claims and current implementation boundary

This protocol defines the evidence required for comparable reviewer evaluation. The repository has an **adjudicated-match metric scorer** and a typed, versioned local run-manifest contract (`src/reviewforge/benchmark/manifest.py`), but not a semantic matcher, dataset loader, confidence-interval implementation, provider, or benchmark runner. `src/reviewforge/benchmark/metrics.py` consumes `matched_gold_id` decisions supplied by a separately versioned matcher or human adjudicator and calculates overall micro precision/recall/F scores and gold-severity diagnostic slices. The manifest validates recorded metadata and its canonical SHA-256 digest; it does not retrieve or independently verify referenced artifact bytes, prove authenticity, validate benchmark eligibility, or produce benchmark results. The scorer does not validate paths/locations, categories, severity taxonomy, run completeness, or uncertainty. A protocol requirement is not evidence that the corresponding capability exists.

No reviewer benchmark is available for this repository. No score, quality comparison, or leaderboard claim is implied by this document.

## 2. Dataset provenance, versioning, and separation

Every dataset release used in a run must have an immutable, access-controlled manifest and a version identifier. For **each source dataset and task**, record:

- Source name, canonical URL or private source identifier, exact release/revision, original license and applicable use/redistribution terms, acquisition date/time in UTC, acquisition method, and provenance/curator.
- Repository host and stable repository identity; full base and head commit SHAs; PR number/URL where legally retainable; merge-base when relevant; immutable snapshot or archive identifiers; and hashes of the reviewed diff and any retained snapshot artifacts.
- Dataset/task IDs, inclusion status, license review, source label lineage, and integrity hashes (SHA-256 or stronger) for the manifest and immutable input artifacts. A hash without retained, accessible bytes is an integrity reference, not a reproducible snapshot.
- Missing or unknown metadata, exclusions, duplicate relationships, contamination checks, and any access to protected labels. Unknown license, source revision, or snapshot identity makes the sample ineligible for a reproducible scored result unless the limitation is explicitly approved and disclosed; it must not be guessed.

Keep three populations separate and visibly labeled:

1. **Public development data** may be inspected for implementation and prompt development; its use for tuning must be logged.
2. **Protected final evaluation data** has restricted access. Do not put labels, source, or outputs in public logs; record access and any exposure. If labels or examples leak into tuning, quarantine the affected set and establish a new holdout.
3. **External benchmark data/results** retain the external benchmark's version, license, official input/output contract, judge, and submission status. Do not combine external scores with an internal holdout or describe a local score as an official result.

Before scoring, run feasible exact and near-duplicate checks over repositories, commits, PRs, patches, and finding descriptions. Record method/version, matches, manual decisions, known limitations, and public-data contamination risk. Deduplicate repeated or cherry-picked PRs across splits. Related fixes or PRs from one repository/release history remain in one split unless a preregistered design justifies otherwise. A contamination check cannot prove absence of training-data exposure.

## 3. Evaluation unit, sampling, and cohorts

- **Primary unit:** one eligible pull request evaluated once at one immutable base/head snapshot pair under one frozen reviewer configuration. Re-running a stochastic configuration is a repeated measurement of the same unit, not a new independent PR.
- **Finding unit:** one adjudicated defect identity within that PR. Multiple independently actionable defects in one PR are separate gold findings; repeated reports of one underlying defect are one finding plus duplicate predictions.
- **Repository unit:** repository-level summaries aggregate PR-level results and must retain repository identity/clustering. Do not treat findings or PRs from one repository as independent repository samples.
- Score findings at PR scope; report clean-PR false positives at PR scope; aggregate a reported micro metric from the declared eligible PR set. Also show sample counts and per-PR or macro summaries so large PRs do not conceal sample composition.

Define eligibility, sampling frame, exclusions, strata, random seed, and planned cohort comparisons before candidate runs. Sample across defect category, severity, language, repository size/maturity, change size, and complexity; include clean PRs and supported as well as unsupported-language cases. Include cross-file/non-local, authn/authz, API/DB/schema, race/idempotency, performance, test/CI, configuration/supply-chain cases where the source set permits. Report unsupported-language cases as unsupported/unverified, not as successful negative reviews.

Publish each cohort's numerator/denominator and uncertainty. Always show the actual `n`; for fewer than 30 independent PRs, label the slice descriptive and underpowered for stable comparative claims. Do not pool away sparse or unsupported slices. Repeated, reverted, backport, or otherwise related PRs must be identified and kept together when their contents can leak across splits.

## 4. Ground truth, ratings, and adjudication

Use the canonical defect categories and severity levels in `docs/REVIEW_SEVERITY_TAXONOMY.md` and any versioned category rubric. An actionable gold defect must identify one underlying failure, triggering preconditions, impact, evidence, affected snapshot, and a location or justified non-local span. Record category, severity, confidence/verification status, source, annotator, rubric version, timestamps, and adjudication history. Severity is impact, not likelihood or model confidence; `critical` and `high` form the high-severity group. Informational notes are not defect gold.

Two qualified annotators independently label findings where feasible, without seeing candidate identity/output during gold creation. Resolve disagreements through a documented third-party or consensus adjudication; preserve the initial labels and rationale. Ground truth distinguishes confirmed defects, plausible-but-unverified claims, uncertain labels, and non-defects. Only confirmed adjudicated defects enter the primary gold denominator. Report uncertain/unverified items separately; never silently promote or discard them.

Keep benchmark feedback, candidate outputs, and human feedback separate from protected gold labels. Candidate findings absent from gold are **novel/unmatched**, not automatically correct or incorrect. Preserve them as a separate blinded adjudication queue; only add confirmed findings in a newly versioned gold release after adjudication, without using protected labels to tune the evaluated candidate.

## 5. Matching policy (`adjudicated-id-v1`)

### Decision boundary and semantic criteria

The scorer's `matched_gold_id` field is a precomputed adjudication decision. It does **not** infer semantic equivalence from text, category, severity, or location. Use a documented matcher version and blind human audit, or direct human adjudication. An uncalibrated language-model judge is not authoritative ground truth. A match requires that the prediction describe the same underlying defect and substantially agree on failure mechanism and triggering conditions; a vague/shared-keyword statement is insufficient. A different category or severity does not by itself erase defect identity; record category/severity agreement separately. A materially different defect, unsupported claim, or unrelated code location is not a match.

### Location and ambiguity

Resolve paths against the exact reviewed head snapshot. Use repository rename/copy metadata to map renamed files; do not match solely by basename. For a changed line, the predicted path and line span must overlap the adjudicated issue span or satisfy a preregistered location tolerance. For deleted lines, map to the corresponding diff/deletion anchor or an explicitly adjudicated neighboring changed line. A multi-line issue may use an adjudicated span. Non-local issues may be matched by semantic identity only when the adjudication record contains enough evidence; score location separately as `non_local`/not applicable rather than inventing an inline anchor. Unresolvable paths, stale snapshots, or invalid anchors cannot earn location credit and are not silently treated as exact matches.

When several predictions or gold findings are plausible matches, the matcher/adjudicator must resolve the candidate-to-gold mapping before metric computation, record ambiguous alternatives and rationale, and apply one-to-one matching. Do not choose whichever mapping improves a score. Publish matcher precision/recall against a blind human audit before relying on automated matching.

### Scoring behavior and duplicate control

The current scorer's implemented policy is:

- Gold identity is `(pr_id, gold_id)`; duplicate gold IDs within one PR are invalid input.
- Prediction identity is `(pr_id, prediction_id)`; repeated prediction IDs within a PR are invalid input. If omitted, current code synthesizes a row-index ID, so production benchmark inputs must supply stable explicit IDs.
- A prediction earns at most one TP when its non-empty `matched_gold_id` identifies a gold finding in the same PR and no earlier prediction has already received credit for that gold ID.
- Null/empty, nonexistent, cross-PR, and duplicate-match predictions each count as one overall FP. Each unmatched gold finding is one FN. A gold issue can be credited once only.
- Input ordering is preserved. A duplicate prediction's identity may affect which row receives credit, so freeze the prediction artifact and matching table before scoring; do not reorder to optimize a result.

This scorer does not validate malformed field types comprehensively. Reject malformed JSON/schema, unknown PR/task IDs, invalid snapshot/path/line references, duplicate IDs, and incomplete task records at the run-ingestion boundary; do not rely on the metric function to validate them. The current scorer does not calculate location accuracy or category slices. Its severity slices are diagnostic and must not be presented as calibrated severity agreement.

## 6. Metrics and interpretation

For the declared eligible finding population, let `TP` be credited one-to-one matches, `FP` unmatched/invalid/duplicate predictions, and `FN` unmatched confirmed gold findings:

- `precision = TP / (TP + FP)`.
- `recall = TP / (TP + FN)`.
- `Fβ = (1 + β²) × precision × recall / (β² × precision + recall)`; report F1 (`β=1`), F0.5, and F2.
- `high-severity recall = matched critical/high gold findings / all eligible critical/high gold findings`. Report critical and high separately when sample size permits.
- `false positives per clean PR = unmatched actionable defect predictions on adjudicated-clean PRs / number of completed eligible clean PRs`. State whether duplicates are included (they are) and show the clean-PR denominator.
- `location accuracy = predictions with adjudicated path/span correctness / matched predictions for which location applies`; report non-local/not-applicable separately. The current scorer does not compute this.
- `duplicate rate = duplicate predictions for an already credited gold issue / all predictions`; also report the raw duplicate count and denominator.
- Report finding metrics by language, severity, category, repository size, and defect complexity, with explicit sample counts. Preserve unrated labels and report them outside canonical severity slices.
- Report run/task completion and failure rates over all predeclared eligible PRs; median/p95 latency and per-PR latency; model and deterministic-tool cost per PR and total cost. Distinguish measured cost, estimated cost, and unavailable cost.

### Empty denominators and unavailable data

Never convert missing labels, unavailable data, skipped tasks, or failed runs into a perfect result or a negative finding. The existing scorer emits numeric `0.0` when a precision, recall, or F-score denominator is zero. Interpret that value with an explicit `undefined`/zero-denominator status: an empty-gold/empty-prediction corpus has no estimable precision or recall and is **not** evidence of either perfect or zero reviewer quality; no predictions with non-empty gold yields recall 0 and undefined precision; predictions with no gold yield precision 0 and undefined recall. A publisher must preserve denominator counts and undefined status rather than present the scorer's fallback zero as a substantive estimate.

If labels are unavailable, do not score that PR as clean. If a run failed, timed out, or was incomplete, do not impute a clean result; report the failure and retain the predeclared task in completion/failure denominators. If clean PR count is zero, false positives per clean PR is undefined. If a location is inapplicable, omit it from that location denominator and report the count.

### Uncertainty and paired comparison

Use a cluster bootstrap with **PR as the resampling unit** (repository clustering must additionally be reflected when multiple PRs per repository are sampled). For each published metric, preregister bootstrap replicate count and seed; default is 10,000 PR-cluster resamples, percentile 95% interval (2.5th–97.5th percentiles). For paired candidates, resample the same PR clusters and report the interval for the paired metric difference. Do not bootstrap individual findings as independent observations. If there are fewer than two independent clusters, the interval is not estimable; with small samples, label it unstable and avoid decisive claims. Report sample counts, method, seed, replicates, and interval alongside point estimates. The current scorer does not calculate intervals or paired comparisons.

## 7. Experimental controls and immutable run record

Freeze before a run: protocol/version and hash; dataset release/manifest and hashes; eligible task list and sampling seed; repository/base/head snapshots; provider and exact model identifier/version; prompt and system-instruction hashes; context/retrieval policy; matcher/judge and rubric versions; deterministic tool versions/configuration; temperature/sampling parameters; retry policy; timeout, token/tool/cost budgets; runtime/container and dependency versions; and candidate/run identity.

Compare candidates on identical immutable PR snapshots, same eligibility rules, and comparable resource/cost budgets. Preserve their original configurations. For stochastic systems, preregister repeat count/seeds and report all runs and variability; never cherry-pick the best seed or tune after viewing protected evaluation results. Development feedback and threshold changes must be logged. Any post-hoc change requires a new run/version and cannot replace the original result.

Each versioned run manifest must be capable of recording:

- Manifest schema/protocol/dataset versions and SHA-256 integrity hashes.
- Run ID, UTC start/end, source commit SHA, immutable base/head and artifact IDs, task IDs, random seed, environment/toolchain/container identifiers.
- Provider/model/configuration, prompt/context/retrieval/matcher/tool versions and config hashes, parameters, resource/cost/time budgets.
- Raw output artifact references and hashes with access classification/retention; do not place API keys, secrets, protected labels, or private source in public manifests/logs.
- Per-task completion/status, latency, measured cost, retries, exclusions, timeout/crash reason, and metric/uncertainty artifacts.
- Aggregate results, denominators, exclusion list and reasons, evaluator notes, audit/adjudication versions, and publication classification.

`src/reviewforge/benchmark/manifest.py` implements a local schema version `1.0.0` with required dataset ID/revision/manifest hash, protocol ID/version/hash, repository base/head commits and snapshot/diff hashes, provider/model and prompt/config hashes, tool versions, explicit budgets, environment fingerprint, lifecycle timestamps, and artifact references. It canonicalizes stable UTF-8 JSON, computes SHA-256 over the payload excluding the digest field, verifies the supplied digest on load, rejects unknown/missing keys and duplicate JSON keys, validates lifecycle semantics, and supports explicit terminal transitions plus atomic local JSON persistence. References are metadata only: artifact bytes are not fetched or hashed by this module, and a digest is not a signature or proof of source provenance. The manifest does not currently record every per-task metric or run execution parameter (for example random seeds, context/matcher versions, task-level costs, access classification/retention, or result adjudication); these remain protocol requirements and are not inferred. The local contract test module is present, but was not executed in this environment because SEC-007 has no verified test sandbox. Treat missing required fields as an incomplete/non-reproducible run, not as defaults.

## 8. Eligibility, exclusions, and failure handling

Define inclusion/exclusion rules before seeing candidate outputs. Eligibility may require legally usable data, immutable snapshot identity, complete enough diff/task metadata, and valid adjudicated labels. Record every candidate-task as eligible, completed, failed, timed out, crashed, skipped, censored, or excluded, with reason, timestamp, and relation to the frozen task set. Keep raw failure/exclusion history; never remove a difficult PR, silently retry away a failure, or revise denominators after seeing results.

Report planned, eligible, completed, failed, timed-out, excluded, and censored counts separately and provide reasons. Retries remain linked to the initial task and are governed by the frozen policy. A run with any incomplete eligible tasks cannot be called complete; report both all-eligible completion/failure metrics and, if useful, clearly labeled completed-task-only quality metrics. Do not conceal their selection bias.

## 9. Publication and claim rules

Every scorecard identifies whether results are **internal measured**, **independently reproduced**, **vendor-reported**, or **officially published by the benchmark**. Only the official benchmark's confirmed submission/leaderboard flow permits an official-score claim. Vendor claims are attributed and never blended with independent measurements.

Publish protocol/dataset versions and hashes, run date, exact model/config/prompt/tool versions, sample and task counts, cohort definitions, all metric denominators and uncertainty, exclusions/failures/completion, latency/cost, matching and audit method, license/terms compliance, and limitations. Keep protected holdout labels/results private according to access policy. External benchmark results remain separate from internal evaluation.

Do not claim superiority without a valid comparable evaluation and uncertainty-aware interpretation. Do not extrapolate across languages, repositories, or configurations absent evidence. A local scorer output is not proof that matching is valid, a reviewer ran, or results are official. “No finding” means “not detected,” never “safe.”

## 10. Implementation status and next evidence

- **Implemented locally:** `score_findings` computes adjudicated-ID micro counts, duplicate/unmatched penalties, precision/recall/F1/F0.5/F2, and gold-severity diagnostic slices.
- **Implemented locally, runtime tests not executed:** typed manifest schema/validator, canonical digest verification, strict semantic validation, run-state transitions, artifact references, and atomic local JSON persistence. See `src/reviewforge/benchmark/manifest.py`; deterministic tests are in `tests/test_benchmark_manifest.py`.
- **Not implemented:** semantic matcher, matcher audit, dataset/snapshot acquisition, category/location/clean-PR metrics, high-severity aggregate, uncertainty/paired comparisons, provider run, external adapter, protected holdout, and published scorecard.
- **Benchmark status:** NOT RUN. No provider is configured and no valid reviewer benchmark result is available.
- Deterministic local scorer tests may use fixed in-memory records; they do not execute submitted-repository code or access a network. Any test that runs repository-controlled commands or benchmark fixtures still requires a verified isolated environment. No provider call, protected data access, network access, target-repository execution, or external publication is authorized by this protocol.
