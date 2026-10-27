# Review Finding Severity Taxonomy

**Status:** Proposed normative product and benchmark-label policy; no runtime enforcement or calibration is implemented.

Severity describes the **impact if the stated failure occurs**, given the finding's stated preconditions. It is not model confidence, likelihood of detection, fix effort, code quality, or an automatic merge decision. Record uncertainty separately. Assign the lowest level that fully represents the supported impact; do not inflate severity to attract attention.

## Canonical levels

Use exactly these lowercase values in normalized benchmark gold and prediction records: `critical`, `high`, `medium`, `low`, `informational`.

| Canonical label | Impact definition | Illustrative review finding | Triage example |
|---|---|---|---|
| `critical` | A credible failure can cause catastrophic or broad impact: systemic compromise, large-scale sensitive-data exposure/loss, irreversible corruption, or an outage that disables a core service for a substantial population. The trigger and reach must be supported, not merely imaginable. | A changed authorization path demonstrably lets unauthenticated callers retrieve sensitive records across tenants. | Escalate immediately; block release/merge pending investigation and mitigation; involve the responsible security/incident owner. |
| `high` | A credible failure has serious material impact to an important security boundary, core operation, or significant user/data population, but does not meet the catastrophic/broad critical threshold. | A changed retry path can charge a customer repeatedly for one accepted operation, with no idempotency guard. | Prioritize before merge or release; assign an owner and verify the correction or an explicit mitigation. |
| `medium` | A material but bounded or conditional failure affects a feature, subset of users, or non-critical data/operation; a reasonable workaround or containment exists. | A changed pagination cursor skips records after a specific boundary, affecting large accounts that use the affected endpoint. | Schedule a timely fix; document affected conditions and workaround; escalate if scope or impact grows. |
| `low` | A limited, localized failure with minor impact, narrow triggering conditions, or straightforward recovery; it does not materially compromise a core service or security boundary. | A changed optional display preference falls back incorrectly for a narrow legacy configuration, without affecting stored data or core use. | Fix opportunistically or in normal maintenance; avoid blocking a change unless local policy or accumulated impact warrants it. |
| `informational` | Context about the change with **no defect or material harmful outcome asserted**. It is explanatory, not an actionable defect finding. | A note that a module now uses a different cache layer, with no claim that the change is incorrect. | No defect-remediation action is implied; use only when the context helps the reviewer understand the change. |

Examples illustrate the boundary, not a universal classification. Actual severity depends on the exact affected assets, reach, preconditions, duration, reversibility, and evidence in the reviewed snapshot. If these are unknown, state the uncertainty; do not infer a higher impact.

## Assignment and tie-breaking

1. Establish the concrete failure mode and material impact under the reviewer quality contract before assigning a defect severity.
2. Estimate impact from supported scope and consequence, including affected users/data, security boundary, service criticality, duration, and reversibility.
3. Use exploitability or trigger likelihood only to describe preconditions and triage urgency; do not treat probability or model confidence as the impact label.
4. When evidence supports multiple plausible outcomes, describe the range and choose the highest level whose impact is actually supported. Do not use a speculative worst case.
5. Severity is separate from priority, confidence, verification status, category, and fix size. Repository policy may change scheduling, but must not silently rewrite the impact label.
6. A note with no alleged defect is `informational`, not a low-severity defect. A speculative or unsupported defect claim is not rescued by assigning `low`; abstain or disclose uncertainty instead.

## Benchmark label mapping

### Normalized records

- Store the canonical lowercase severity string in the `severity` field for **both** adjudicated gold findings and predictions.
- Keep severity orthogonal to issue `category` (for example, correctness or security); do not encode category inside the severity value.
- The existing JSONL examples use `severity` strings such as `high` and `low`. Apply this five-value vocabulary to new normalized records.
- `critical` and `high` form the **high-severity** group for the charter's high-severity-recall measure. Report each level separately as well when sample sizes permit; disclose the denominator and uncertainty.
- `medium` and `low` remain separate severity slices. They are not included in high-severity recall.
- `informational` records are not defect gold findings and must not be placed in defect gold labels or the defect-prediction population scored for precision/recall or false positives. If product output includes informational notes, retain/report them in a separate, explicitly non-defect population; do not give them true-positive credit for a defect.

### External and invalid labels

- For an external dataset or tool, preserve the original severity label and record the source plus a versioned mapping before normalization. Map only when the source definition supports an unambiguous impact-equivalent canonical label; do not map by label name alone.
- If a source label is missing, ambiguous, or not equivalent, retain it as unrated/source-specific metadata and mark it out of the canonical severity slices. Do not coerce it to `low`, `informational`, or another convenient value. Disclose the count and treatment.
- A valid issue may remain in overall adjudicated finding matching while being omitted from severity-specific analysis if its severity is unrated; report that omission explicitly. A malformed label must not silently become a canonical label.
- Report severity-label agreement separately from defect matching. A matched finding can be a defect true positive while having a severity disagreement; do not hide the disagreement inside the match decision.

These conventions describe intended benchmark semantics. The current scorer accepts arbitrary severity strings (it lowercases them for grouping) and does not validate this taxonomy, map vendor labels, or provide the combined critical/high slice. Those behaviors remain unimplemented.

## Change control

Changing a definition, example boundary, canonical value, external mapping, or high-severity grouping requires a dated versioned decision before using the revised mapping in a benchmark run. Do not rewrite historical gold labels or compare runs with different mappings as if they were directly equivalent.
