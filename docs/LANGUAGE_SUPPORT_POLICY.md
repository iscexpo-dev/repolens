# Language Support and Evaluation Policy

**Status:** Proposed product policy. This document does not assert that any language is currently implemented, supported, or evaluated.

## Tier definitions

| Tier/state | Meaning | User-facing treatment | Evidence required to enter or remain in state |
|---|---|---|---|
| **Tier 1 — evaluated support** | The product has an explicitly scoped, repeatedly evaluated review path for the stated language and supported workflow. “Tier 1” is a future promotion state, not a current claim. | May be described as supported only within the evaluated scope. Disclose relevant limitations, partial checks, and failure/abstention behavior. | A versioned per-language benchmark slice on immutable snapshots, sufficient representative samples, adjudicated matching, clean PR controls, task completion/failure rates, severity/category slices where sample sizes permit, and uncertainty. Preserve tool/model/config versions and an independent review of the evaluation. |
| **Provisional — insufficient evidence** | The input appears to use a language for which implementation or evaluation is incomplete, absent, or too small to support a coverage claim. | State “provisional/unverified”; do not promise defect detection or imply that a clean result establishes safety. Suppress or clearly qualify any findings that depend on unavailable parsing, context, or checks. | Record exactly what was and was not evaluated. Promotion requires the Tier 1 evidence gate; a parser accepting text or a model recognizing syntax is not sufficient evidence. |
| **Partial workflow coverage** | Some files or checks can be processed, but coverage is incomplete—for example, mixed-language changes, generated/vendor files, unsupported dialects, macros, templates, embedded languages, binary files, truncated diffs, or missing cross-file context. | Mark the review partial and name affected files/checks or the reason. Do not present it as a complete clean review. Findings from processed portions retain their own evidence/uncertainty limits. | Per-file/workflow limits and successful/failed/skipped checks are explicitly reported. Evaluation measures partial/failure rates and does not count omitted or unprocessed content as a pass. |
| **Unsupported** | The relevant language, dialect, artifact type, or workflow has no validated review path, or safe interpretation cannot be established. | Abstain from language-specific conclusions. Report unsupported scope and any checks not run. Do not return “no findings” as if review completed. | Explicitly document the unsupported condition; re-entry requires the same per-language evaluation gate as a new support claim. |

## Current project status

**No Tier 1 language is identified or claimed by this policy.** The repository contains a unified-diff changed-line parser and a starter API, but no configured reviewer, language-support registry, per-language evaluation, or benchmark result. A parser can identify textual added lines; that is not language-aware review coverage. The TODO’s Tier 1 acceptance is a requirement to publish policy and evidence gates, not evidence that a language already meets them.

No language list should be advertised as supported until its exact scope (language/version or dialect, file types, relevant workflows, exclusions, and checks) has per-language evaluation evidence meeting the Tier 1 gate. Familiarity of a model with a language, popularity, syntax highlighting, parser availability, or success on another language is not a substitute.

## Required abstention and partial-review behavior

- Treat detection of language and file type as uncertain when extension, content, generated status, or embedded-language boundaries are ambiguous. Do not guess a supported state from a filename alone.
- Mixed-language repositories and files must be evaluated per relevant language/workflow. A supported component does not make the whole change fully supported.
- For unsupported syntax, dialects, generated code, embedded regions, binary content, truncated input, missing context, tool errors, or timeouts, report the limitation and mark the affected review scope partial, unavailable, or unverified as appropriate.
- Do not infer “no defect” from code that was not parsed, retrieved, analyzed, or checked. “No findings” means only no issue was detected in the input/checks actually examined; it is not proof of safety.
- A candidate finding may still be shown only if it independently meets the reviewer quality contract. Disclose unsupported context or verification limits; otherwise abstain rather than make a language-dependent claim.
- Review remains read-only. Language uncertainty does not authorize repository execution; tests or analyzers on untrusted code require the separately approved, verified sandbox boundary.

## Per-language promotion and expansion gate

Before adding a language to Tier 1, publish an evaluation record that specifies:

1. Language, version/dialect, file types, repository/workflow scope, supported constructs, and explicit exclusions.
2. Immutable dataset/repository revisions and PR base/head identities; sample counts for defect-bearing and clean changes.
3. Coverage across applicable issue categories, including cross-file behavior and language-specific risks; unsupported/partial cases and their disposition.
4. Provider/model, prompts/configuration, parser/analyzer/tool versions, context policy, budgets, and sampling settings.
5. Adjudicated matching procedure or documented matcher with blind human audit; separate grounded and novel findings.
6. Precision, recall, F metrics, high-severity recall, false positives per clean PR, category/language slices where supported by sample size, completion/failure/abstention rate, cost, latency, and uncertainty intervals when measured.
7. Failed runs, exclusions, censored tasks, and evaluator notes, retained and disclosed rather than silently removed.
8. A predeclared acceptance decision and review owner. If the sample is too small or uncertainty too wide for the intended claim, remain provisional/partial rather than promoting.

Expansion to new language versions, frameworks, embedded syntaxes, or workflows is a new scoped claim. Re-evaluate material changes to models, prompts, parsers, context, or tools before carrying forward a previous language-support statement. Do not tune on protected holdouts.

## Reporting rule

Every user-facing or benchmark statement must distinguish **implemented**, **evaluated**, **partial**, **unsupported**, and **not measured**. A language can have prototype code without evaluated support, and benchmark evidence for one scope does not establish universal language coverage. No runtime language detector, enforcement, or Tier 1 evaluation is implemented by this document.
