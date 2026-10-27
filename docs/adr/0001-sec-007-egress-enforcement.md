# ADR-0001: SEC-007 Egress Enforcement Boundary

- **Status:** Proposed; no deployment architecture approved
- **Date (UTC):** 2026-10-24
- **Owner:** Unassigned platform/network enforcement owner
- **Reviewers/approver:** None recorded
- **Affected tasks:** SEC-007, SEC-008
- **Supersedes / superseded by:** None

## Context

SEC-007 requires repository-controlled execution to have default-deny network
access with narrow trusted exceptions and protection against DNS/IP, metadata,
and internal-network bypasses. The checked-out tree contains
`docs/SANDBOX_EGRESS_POLICY.md`, application source, tests, `pyproject.toml`,
and an issue-automation GitHub workflow. Inspection found no sandbox worker,
deployment/container/VM manifest, network namespace or firewall policy,
egress gateway, DNS service, cloud configuration, or adversarial network
tests. The API shell has no execution path. No runtime, network topology, or
enforcement owner is identified; the workspace is not verified as an isolated
test worker. These are observations about this checkout, not proof that
infrastructure does not exist elsewhere.

Repository code must not execute until a real external boundary has been
selected, implemented, and verified. A worker-local policy or mock gateway
does not establish containment.

## Alternatives considered

| Option | Boundary, privilege, and network behavior | Isolation, operations, cost, and failure/test considerations |
|---|---|---|
| Do nothing / rely on the policy document | No enforcement point; DNS, IPv4/IPv6, metadata, and arbitrary egress remain uncontrolled. | Lowest immediate effort but unacceptable for repository execution; no meaningful isolation test can pass. |
| Per-job ephemeral VM with host/cloud network controls | Hypervisor or cloud network policy controls each VM identity; DNS and both IP families must be routed through controlled infrastructure or denied. Metadata and control-plane routes must be blocked outside the guest. Requires cloud/platform privileges. | Stronger kernel boundary and tenant separation potential, with higher provisioning cost and latency. Fail closed by withholding the VM/job on policy setup errors. Test from disposable guest VMs against actual routes and gateway logs. |
| Per-job container/network namespace plus host firewall | Privileged host controller assigns a unique network identity and installs host-enforced default-deny rules before launch. DNS and all IPv4/IPv6 paths must be denied or gateway-routed; host, metadata, and internal routes blocked outside the container. Requires host networking/firewall privileges. | Lower startup/resource cost, but shares the host kernel and demands careful namespace, capability, route, and cleanup controls. Any policy-install failure must prevent execution. Test from disposable jobs on the actual worker host. |
| Restricted workers behind an external egress gateway | Worker has no direct route; gateway/firewall authorizes job-bound destination/protocol/port exceptions and validates resolved and connected addresses. DNS, redirects, proxies, and IPv6 must not bypass the gateway. Requires network/platform owner and gateway policy authority. | Central audit and policy revocation are possible; availability and routing become dependencies. Gateway failure must deny, not fail open. Test actual worker routes and both allowed and denied paths. |
| Managed sandbox product | Vendor/tenant control plane enforces per-job network policy; DNS, IPv4/IPv6, metadata protection, and audit must be evidenced by product configuration and independent tests. Requires an approved vendor and administrative integration. | Potentially less platform operations work, with recurring cost and provider dependency. Isolation claims, failure behavior, data handling, and test access are unknown until a product is selected. |

## Decision

**Defer selection of a concrete runtime and enforcement architecture.** Current
repository and environment evidence does not identify a platform on which a
specific option can be implemented or independently tested. The reference
requirements are: untrusted jobs have no direct route; a host/platform-
controlled boundary applies per-job default deny before execution; trusted
policy grants narrow, expiring exceptions; DNS results and actual connected
IPv4/IPv6 destinations are checked; and metadata, control-plane, host, internal,
and neighboring-job paths are denied. These are requirements, not deployed
controls or an approved architecture.

An authorized platform owner must select the runtime/topology, name the
enforcement owner, approve required privileges, and provide a disposable,
resource-limited, credential-free test environment before implementation.

## Consequences

- SEC-007 remains **BLOCKED**; SEC-008 remains gated on SEC-007.
- No host firewall, cloud route, shared worker, or production configuration is
  changed speculatively.
- No repository-controlled code, builds, or sandbox probes are authorized by
  this ADR.
- After platform selection, update/supersede this ADR with the concrete owner,
  policy distribution and audit mechanism, routes, DNS behavior, failure
  semantics, cleanup contract, and approval record.

## Validation and evidence

- Source/configuration inspection: completed for this run; no deployment or
  network-enforcement artifact was found in the checkout.
- Runtime enforcement and adversarial tests: **NOT RUN**; no selected runtime
  or verified worker is available.
- Required test cases and evidence criteria: `docs/SEC-007-ACCEPTANCE-TEST-MATRIX.md`.
- Approval, cloud/provider-specific route review, independent security review,
  and real worker tests remain outstanding.
