# Product Charter

**Status:** Proposed product charter for the Best AI Code Reviewer 2026 project. This describes intended scope, not implemented capability.

## Accountable Owner

The accountable role is the repository owner acting as project maintainer and release owner. The execution pack does not identify an individual by name; the repository owner must designate one before pilot or release signoff. Engineering, security, benchmark, and operations contributors are responsible for evidence in their respective areas, but do not replace the accountable owner.

## Primary Users

- Individual developers seeking high-signal, evidence-backed review before requesting teammate approval.
- Engineering teams reviewing changes across services, packages, or legacy code.
- Security engineers seeking an additional review layer alongside established security tools.
- Platform and DevEx teams applying consistent, auditable review policy across repositories.
- Researchers and engineering leaders comparing review configurations under reproducible conditions.

## User Need and Product Outcome

Help developers find and resolve material defects introduced by a proposed change while minimizing false alarms, review burden, privacy exposure, and cost. The north-star outcome is verified, actionable defects prevented per unit of developer attention and review cost. A generated comment is not itself evidence of product value.

## Target MVP Workflow

1. Receive an authorized pull-request event and capture immutable base/head commit identities.
2. Parse the change and disclose incomplete, unsupported, or truncated input.
3. Select relevant repository context and configured deterministic analysis evidence.
4. Produce structured candidate findings using a configured reviewer; repository content remains untrusted data.
5. Validate evidence, changed-line anchors, duplicates, severity, and policy before presenting findings.
6. Show findings and completed/failed/unavailable checks to the developer; collect feedback without silently rewriting benchmark labels.
7. Keep the integration read-only by default. Any future fix proposal is separately authorized and is not merged automatically.

This is the intended workflow only. The current repository does not implement the end-to-end workflow.

## Non-Goals and Safety Contract

- Guaranteeing detection of every bug, proving a repository safe, or claiming universal superiority.
- Automatically approving or merging pull requests in the MVP.
- Running untrusted repository code in the API process or with developer/production credentials.
- Treating absence of findings, skipped checks, unsupported languages, or timeouts as a pass.
- Treating model confidence as a calibrated probability without held-out calibration evidence.
- Publishing benchmark scores without frozen inputs, documented matching, uncertainty, and reproducible artifacts.
- Treating user acceptance/dismissal as adjudicated ground truth without a separate review process.

Every finding must describe a concrete failure mode and material impact, cite relevant evidence, be actionable and non-duplicative, and state uncertainty or verification limits. No findings means only that no issue was detected by the checks that actually ran; it is not proof of safety, correctness, or absence of defects. See [`REVIEWER_QUALITY_CONTRACT.md`](REVIEWER_QUALITY_CONTRACT.md) for the normative actionability, context, evidence, and abstention requirements. These are product requirements, not verified runtime behavior.

Severity labels describe supported impact, not model confidence or fix priority. The proposed `critical`/`high`/`medium`/`low`/`informational` definitions, triage examples, and benchmark mapping are in [`REVIEW_SEVERITY_TAXONOMY.md`](REVIEW_SEVERITY_TAXONOMY.md); they are not yet enforced or calibrated by the implementation.

Language support is a scoped, evidence-based claim, not a model-capability assumption. The proposed Tier 1, provisional, partial, and unsupported states, abstention rules, and per-language promotion evidence are in [`LANGUAGE_SUPPORT_POLICY.md`](LANGUAGE_SUPPORT_POLICY.md). No language is claimed as implemented or evaluated by that policy, and no per-language benchmark evidence is currently available.

Repository and organization review settings require deterministic, auditable resolution. The proposed categories, severities, budgets, excluded paths, required checks, and scope precedence are specified in [`POLICY_CONFIGURATION.md`](POLICY_CONFIGURATION.md); this is a contract only, not an implemented configuration or enforcement mechanism.

## Success Measures

These are required measurements, not achieved results. Numeric release thresholds must be approved and recorded before the protected evaluation set is run; no thresholds or reviewer-quality measurements are currently established.

| Measure | Definition | Required interpretation |
|---|---|---|
| Grounded precision and recall | Adjudicated true-positive findings divided by predictions and gold findings, respectively | Report together with F1/F0.5/F2, sample counts, and uncertainty; describe the matching method and audit quality. |
| High-severity recall | Adjudicated high/critical gold findings detected divided by high/critical gold findings | Report severity definitions, denominator, and confidence interval; an underpowered slice is inconclusive. |
| False-positive burden | Unmatched findings per clean PR and per reviewed PR | Include clean PR controls and developer attention burden; do not hide unmatched predictions. |
| Actionable value | Human-adjudicated accepted or fixed material findings per PR and per unit of developer review time | Keep human-adjudicated outcomes separate from model assertions and raw comment counts. |
| Coverage and completion | Completed, partial, failed, timed-out, and unsupported review tasks by language/category | Missing checks and unsupported inputs are not successful completions. |
| Efficiency | Cost per completed PR and median/p95 end-to-end latency | Include retries and analyzer/model costs; state budgets and censoring. |
| Comparative quality | Paired metric differences on identical immutable snapshots and budgets | Report uncertainty and all failures/exclusions; no universal ranking from incomparable datasets. |

Before any quality claim, freeze the dataset and configuration, establish human-audited matching, and preregister thresholds. Benchmark and pilot results are currently **not run**.

## MVP Boundary

The intended MVP includes a GitHub pull-request path, immutable snapshots, a configured model adapter, repository context, deterministic analysis, validated findings, an offline benchmark, and read-only output. Safe patch generation, automatic merge, additional providers, production deployment, and broad language claims remain outside the initial MVP boundary unless separately approved and evidenced. The existing project is still a foundation scaffold: it currently provides diff parsing, adjudicated metric scoring, and an API shell only.
