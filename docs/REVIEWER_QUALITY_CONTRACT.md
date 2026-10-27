# Reviewer Quality Contract

**Status:** Normative product requirement; this contract does not describe verified runtime behavior.

The reviewer exists to surface material, change-related defects with enough context and evidence for a developer to decide what to do. It should optimize for useful defect prevention, not comment volume. This document clarifies the finding-quality rule summarized in `PRODUCT_CHARTER.md`; it does not define severity levels, benchmark thresholds, or a specific finding schema.

## 1. Finding requirements

A finding presented as actionable must satisfy all three requirements below. If the available evidence cannot support them, the system must abstain from presenting it as a confirmed defect, or clearly label the result as uncertain and unverified rather than overstating it.

### Actionable

- Identify the changed behavior and a concrete condition under which it can fail.
- State the material consequence for a user, system, data, security boundary, or operational outcome. Explain impact rather than relying on an unexplained severity label.
- Give a practical next step that addresses the described failure. Prefer a minimal, specific recommendation over a speculative rewrite.
- Exclude style preferences, generic best-practice advice, and hypothetical concerns with no plausible triggering condition or material impact.
- Avoid duplicate findings for the same underlying issue; combine related observations when separate comments would not enable separate action.

### Contextual

- Explain how the relevant changed code interacts with surrounding code, inputs, state, control/data flow, configuration, or an existing invariant.
- Identify necessary preconditions and scope. If the failure depends on an assumption, make that assumption visible.
- Describe why the issue is attributable to this change, or explain when attribution cannot be established.
- Use language appropriate to the evidence: distinguish a demonstrated failure from a plausible risk, and do not present model confidence as a calibrated probability without separate calibration evidence.

### Evidence-backed

- Provide traceable support for the failure mechanism: the exact reviewed snapshot identity and relevant file/line locations, or the specific check/tool result and version that supports the claim.
- For an inline finding, validate the anchor against the exact reviewed snapshot and an eligible changed line. If no valid changed-line anchor exists (for example, a non-local issue), use an appropriately scoped summary with supporting locations or suppress the inline comment; never invent an anchor.
- Include enough evidence for a reviewer to understand or reproduce the stated condition without exposing secrets or unrelated source.
- Separate observed facts (such as a test failure or reachable path) from inference. State what was and was not verified. Do not say a test, analyzer, or reproduction passed unless it actually ran and its result is available.
- If evidence is missing, contradictory, stale, or tied to another snapshot, do not present the claim as verified. Abstain or clearly report the limitation.

## 2. Review outcome and uncertainty

“No findings” means only that the checks which actually ran did not detect a reportable issue in the input they actually examined. **It is not proof that the change or repository is safe, correct, or defect-free.** The reviewer must never imply exhaustive inspection or guaranteed detection.

Every review result must distinguish, where applicable:

- completed checks and their scope;
- failed checks and their failure reason;
- skipped or unavailable checks and why they did not run;
- partial, truncated, unsupported, stale, or timed-out input;
- findings requiring additional verification or assumptions.

An absent result, provider/tool error, unsupported language, omitted context, or timeout is **unverified**, not a pass. A partial or unavailable review must not be rendered as a completed clean review. If the system cannot establish a finding’s required actionability, context, and evidence, it must prefer abstention or an explicit uncertainty statement over an unsupported assertion.

## 3. Presentation constraints

- Present findings as review assistance, not as approval, proof of safety, or a substitute for human ownership.
- Keep review read-only by default. A finding does not authorize repository writes, patch execution, approval, or merge.
- Make the explanation concise enough to assess, while preserving the evidence, triggering condition, impact, and uncertainty needed to judge it.
- Do not claim a finding is fixed or verified unless the relevant change and checks were actually observed.

## 4. Quality claims and evaluation

This contract defines desired behavior; it is not evidence that the implementation satisfies it. Product quality claims require evaluation under the versioned benchmark protocol, including adjudicated matching or a documented matcher with blind human audit, clean pull-request controls, disclosed failures/exclusions, sample sizes, and uncertainty. No numeric quality target or achieved result is established here. User feedback alone does not silently become benchmark ground truth.

## 5. Non-goals

This contract does not guarantee defect detection, define a complete language-support matrix, define severity taxonomy, prescribe a model/provider, or assert that current output has been tested against these criteria. A review with no findings means only “not detected,” never “safe.”
