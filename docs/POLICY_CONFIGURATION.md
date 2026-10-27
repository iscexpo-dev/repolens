# Organization and Repository Policy Configuration

**Status:** Proposed configuration contract only. No policy schema, resolver, storage, API, or audit event implementation currently exists.

This specification defines how organization and repository policy settings are intended to control a future review run. It covers only categories, severities, review budgets, excluded paths, required checks, deterministic precedence, and the audit record needed to explain the result. It does not authorize write actions or repository-code execution.

## Policy inputs

Each policy document is versioned and scoped to exactly one organization or repository. A resolved review run uses:

1. The versioned product safety defaults and immutable platform limits.
2. The applicable organization policy, if one exists.
3. The repository policy, if one exists and is authorized for that repository.

Organization policy establishes defaults and non-relaxable constraints. A repository may narrow the review scope or strengthen controls, but may not weaken an organization-mandated restriction, increase an organization budget ceiling, remove an excluded path, or omit an organization-required check. Missing policy fields mean **inherit**; an explicitly empty set means **nothing enabled**, not “use defaults.” Invalid, unauthorized, stale, or conflicting policy is rejected and the run fails closed or is marked unavailable; it is never silently replaced with a permissive default.

Task/run-level controls, if introduced later, may further narrow scope or budgets only; they do not override these policy layers. This is a design constraint, not an implemented feature.

## Configurable settings

| Setting | Organization value | Repository value | Resolution rule |
|---|---|---|---|
| Review categories | Allowed/default category set, using a versioned category registry | Optional requested subset | Effective categories are the repository subset intersected with the organization set. If only one scope supplies a value, inherit it. An empty effective set means no category review; report that explicitly. Unknown category IDs reject the policy revision. |
| Finding severities | Allowed/default severity set using the canonical values in `REVIEW_SEVERITY_TAXONOMY.md` | Optional requested subset | Effective severities are the repository subset intersected with the organization set. A repository cannot enable a severity excluded by organization policy. Empty means no severity is enabled, not “all.” Severity never overrides evidence requirements or means approval. |
| Review budgets | Maximum allowed cost, elapsed time, and model/tool resource ceilings, where supported | Optional lower ceilings | For each configured dimension, effective budget is the minimum of all applicable ceilings and immutable platform limits. A missing dimension inherits; zero means no allocation for that resource. Units and currency are explicit and versioned. |
| Excluded paths | Mandatory repository-relative path patterns | Additional repository-relative exclusions | Effective exclusions are the union. A repository cannot re-include a path excluded by organization policy. Excluded content is reported as not reviewed; exclusions do not imply a pass. Pattern syntax/version and path normalization are fixed by policy schema. |
| Required checks | Mandatory check IDs from a versioned check registry | Additional required check IDs | Effective required checks are the union. A repository cannot remove an organization-required check. Each check must have an explicit success, failure, skipped, unavailable, or timed-out result; absent execution is not success. Unknown check IDs reject the policy revision. |

Category and check identifiers must be stable, namespaced values, not free-form instructions. Policy values are data, not authority to expand tool permissions, execute arbitrary commands, alter safety boundaries, or change benchmark labels.

## Deterministic precedence and resolution

Precedence is field-specific and monotonic rather than “last writer wins”:

1. Immutable product/security constraints always apply and cannot be relaxed by either scope.
2. Organization policy supplies defaults and mandatory ceilings, restrictions, exclusions, and checks.
3. Repository policy may select a subset, lower a budget, or add exclusions/checks.
4. Missing values inherit from the preceding applicable layer; empty values retain their explicit meaning.
5. Conflicting or invalid values are rejected with a stable error code and source location. The resolver must not guess, silently drop the conflict, or fall back to a less restrictive policy.

Resolution is performed against a fixed organization/repository identity and policy revisions before review work starts. The result is an immutable effective-policy snapshot bound to the review run. A change to either policy during a run applies only to a later run; it must not mutate the active run's effective configuration.

### Example

An organization allows categories `{correctness, security}`, allows severities `{critical, high, medium}`, caps review cost at `$2.00`, excludes `generated/**`, and requires checks `{diff-parse, secret-scan}`. A repository requests categories `{correctness}`, severities `{high, low}`, cost `$0.50`, excludes `vendor/**`, and adds `unit-tests`.

The effective policy is:

- Categories: `{correctness}`.
- Severities: the repository policy is invalid because `low` is outside the organization-allowed set; resolution fails closed until the repository request is corrected to a subset (for example, `{high}`).
- Cost ceiling: `$0.50`.
- Excluded paths: `generated/**` and `vendor/**`.
- Required checks: `diff-parse`, `secret-scan`, and `unit-tests`.

This example defines resolution semantics only. It is not evidence that these policies can currently be configured or enforced.

## Validation and failure behavior

- Validate the policy schema version, scope identity, authorization, known category/severity/check identifiers, path-pattern syntax, budget units/ranges, and revision before resolution.
- Reject unknown fields or unsupported schema versions unless a documented compatibility rule explicitly handles them.
- Do not accept policy text as executable code or instructions to the reviewer. Settings cannot grant network, filesystem, credential, publishing, or merge permissions.
- If policy cannot be fetched, authenticated, validated, or bound to the run, do not proceed under a permissive default. Mark the policy/review unavailable and disclose why.
- Required checks that did not run or did not complete successfully remain failed/unverified according to their outcome; the overall review must not be called complete when mandatory checks are missing.
- Excluded paths and disabled categories/severities must be visible in the review's scope/coverage disclosure where relevant.

## Auditability

For every policy edit and resolved run, the system should retain an append-only, access-controlled audit record containing:

- organization and repository identifiers;
- policy schema version, immutable revision IDs, and content digests for each applicable scope;
- actor/service identity, authorization result, and event timestamp for policy changes;
- review run ID and exact source snapshot identity for resolution;
- resolver version and deterministic field-resolution rules version;
- effective values plus per-field provenance (inherited, organization-mandated, repository-narrowed, or combined), with sensitive values redacted as needed;
- validation errors, rejected overrides/conflicts, and the resulting fail-closed decision;
- required-check IDs and their observed outcomes, including missing/skipped/failed/timed-out states.

Audit records must not contain source code, credentials, secrets, or unnecessary raw policy text. A policy change creates a new revision; historical run records remain bound to the revision and effective policy actually used. Authorized reviewers must be able to reconstruct why a setting took its effective value without relying on mutable current configuration.

## Implementation and acceptance boundary

The above is a proposed product specification for PROD-005. It does not assert that organization/repository configuration, precedence resolution, permission enforcement, policy storage, or audit events are implemented. The future policy API and effective-policy behavior require separate implementation and tests. Repository policy must not directly mutate benchmark gold labels or redefine the severity taxonomy.
