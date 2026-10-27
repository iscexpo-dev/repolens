# Proposed Sandbox Egress Policy — SEC-007

**Status:** Design artifact only. This repository contains no sandbox worker, egress enforcement point, network policy, or network-isolation tests. This document does not block traffic and is not evidence that any sandbox is contained. SEC-007 remains TODO/partial until enforcement and adversarial verification exist.

## 1. Security objective and boundary

Repository-controlled tests, builds, and fix commands must not have network access by default. A job may reach an endpoint only when a trusted, separately authorized policy grants a narrow, time-bounded exception for that job. Repository files, package scripts, test output, model responses, and sandbox processes cannot request, grant, broaden, or persist an exception.

The egress decision belongs to a host-controlled boundary outside the repository process: preferably a per-job network namespace or equivalent isolated network identity whose only route is through an enforcing gateway/firewall. A policy check inside the same worker process is insufficient because repository code executes within that trust zone. The worker must have no direct route to physical interfaces, host services, other jobs, or cloud control-plane endpoints.

This policy applies to any future sandbox running untrusted code. It does not authorize repository execution. Execution remains prohibited until sandbox isolation, resource controls, secret separation, and the required security tests are implemented and independently verified.

## 2. Default-deny decision

For each new job, the network policy begins in **DENY ALL**:

- no inbound connections to the job;
- no outbound IPv4 or IPv6 connections;
- no DNS, UDP, TCP, ICMP, multicast, broadcast, or alternate resolver path;
- no inherited proxy settings, host networking, host sockets, host resolver mounts, or access to a host-side control socket;
- no access to loopback services other than explicitly documented worker-local functions that cannot proxy to the host or other jobs;
- no direct-IP access and no access to private, link-local, loopback, carrier-grade NAT, reserved, multicast, or otherwise non-public destination ranges;
- no access to cloud metadata endpoints, instance identity services, container/orchestration control planes, credential endpoints, or internal management APIs; and
- no environment variable, repository configuration, command-line argument, or model output can turn networking on.

The default must be enforced by a control plane outside the worker and fail closed if policy retrieval, gateway setup, address classification, or enforcement health is unavailable. A missing, malformed, expired, or ambiguous policy means DENY ALL.

## 3. Explicit allow exceptions

An exception is opt-in and must be approved by trusted policy outside the repository. The policy record should include:

| Field | Requirement |
|---|---|
| `job_id`, `tenant_id`, `snapshot_id` | Bind the exception to one authorized job and immutable snapshot. |
| `requester`, `approver`, `approval_reason` | Identify the trusted actor and justification; repository/model output is not an approver. |
| `destination` | Exact service identity, not a wildcard or arbitrary user-supplied URL. |
| `port`, `protocol`, `direction` | Narrowly specify the minimum required transport and outbound-only direction. |
| `resolved_addresses` | Validate every IPv4/IPv6 result at connection time; reject prohibited/internal ranges even if a hostname was approved. |
| `valid_from`, `expires_at` | Short duration, bound to the job; revoke on job completion or cancellation. |
| `policy_revision`, `audit_event_id` | Preserve the policy and approval provenance for later review. |
| `data_classification`, `purpose` | Record what data may be sent and why; network permission alone does not authorize source disclosure. |

No user or repository-controlled process may edit the active exception for its own job. Do not support wildcard hosts, wildcard ports, arbitrary DNS, general web access, or “allow all package repositories” as an exception. If a dependency download is approved, prefer a trusted pre-fetch/cache service that validates and stages artifacts before the untrusted job rather than granting the job open egress.

## 4. DNS, IP, and metadata protections

DNS and IP controls must be designed together. Blocking a few named metadata hostnames is not sufficient.

1. **DNS:** The default worker cannot reach any resolver. If a narrowly approved hostname is required, resolution occurs through a trusted gateway; the gateway validates all returned A/AAAA records against policy and prohibited ranges. The connection is pinned to an approved resolved address for the request, while TLS/application identity is checked against the approved hostname. Reject redirects or re-resolve and re-authorize every redirect target.
2. **Direct IP:** Apply destination checks to the actual connected address, not only the requested hostname. Deny private, loopback, link-local, metadata, internal service, and non-routable ranges for both IP families. Normalize IPv4-mapped IPv6 and other address representations before policy comparison.
3. **Rebinding and resolution changes:** Do not allow a hostname approved at one time to authorize a later connection to a different or newly prohibited address. Revalidate at connection time and after redirects/retries.
4. **Metadata and control planes:** Explicitly deny cloud metadata and identity services, cluster/node APIs, container runtimes, host management interfaces, and organization-internal control endpoints. Maintain the deny set for the deployment's actual network topology; do not assume one vendor's canonical metadata address is exhaustive.
5. **Alternate paths:** Prevent DNS-over-HTTPS/TLS, proxy tunneling, VPN/tunnel protocols, raw sockets, and application-layer relays from bypassing the enforced gateway. Restrict worker capabilities and routes so such clients cannot establish an alternate path.
6. **IPv6:** If IPv6 is not explicitly supported by the boundary, disable it for the job network rather than filtering only IPv4. If enabled, apply equivalent routing, address classification, DNS, metadata, and logging controls.
7. **Internal services:** A gateway must not become a general-purpose proxy into control-plane or tenant networks. Route only to the explicitly approved destination and port, and prevent access to the gateway's own management interface.

Exact CIDR deny lists and cloud-specific addresses must be maintained as configuration tied to the deployed environment. A static list in this document is not a substitute for route isolation and current provider-specific review.

## 5. Enforcement architecture and lifecycle

Proposed flow:

1. Trusted orchestration validates the job authorization and immutable snapshot identity.
2. A privileged sandbox controller creates a per-job network identity with no direct egress route and installs the default-deny policy before untrusted code starts.
3. The worker receives only its snapshot and explicitly approved inputs; it receives no cloud credentials, provider tokens, developer secrets, host mounts, or access to control-plane sockets.
4. If approved, an external gateway applies the exact job-bound allow rule. It records destination decisions without logging repository source or secret-bearing payloads.
5. The gateway checks DNS results, all resolved/connected IPs, port/protocol, job identity, policy expiry, and every redirect/reconnect. Any failure denies the connection.
6. On timeout, policy-service loss, gateway failure, job cancellation, or job completion, egress remains denied and the exception is revoked. Cleanup is verified before the worker is considered terminated.
7. The controller records policy revision, job/snapshot identity, allowed and denied connection metadata, error/timeout state, and cleanup result in an access-controlled audit trail. Logs must not contain secrets or source by default.

The sandbox must not be able to modify the controller, gateway policy, network routes, or its own identity. A network filter inside the same container without isolation from host networking is not sufficient evidence of enforcement.

## 6. Abuse and failure scenarios

| Scenario | Required outcome |
|---|---|
| Repository script sets proxy variables or changes resolver configuration | No route or permitted proxy exists; attempt is denied and observable. |
| Hostname resolves to a prohibited/private/metadata address or changes after approval | Gateway rejects the resolved/connected address; no fallback direct route. |
| Process connects directly to a public or private IP without DNS | Denied unless the exact address is separately authorized and still passes prohibited-range checks. |
| DNS query uses UDP, TCP, encrypted DNS, or a hard-coded resolver | Denied by default; approved hostname resolution remains gateway-mediated. |
| Redirect points to a different host, port, IP family, or internal address | Re-authorize the new target; otherwise deny. |
| Policy service or gateway is unavailable, policy expires, or job identity is ambiguous | Fail closed; revoke/retain DENY ALL; report job as unavailable/failed, not as a network pass. |
| Worker attempts metadata, host, peer-job, cluster, or internal-service access | Deny at an independent network boundary; do not rely on hostname-only rules. |
| Repository asks the agent/model to enable a network endpoint | No authority; only trusted external approval can create the job-scoped exception. |

## 7. Adversarial verification required before SEC-007 can be DONE

Tests must run against the actual deployed enforcement boundary from inside a disposable, resource-limited test worker. Unit tests of a policy parser alone are insufficient. Use controlled test endpoints and preserve logs/results; do not target third-party infrastructure.

Required cases include:

- deny all ordinary outbound IPv4/IPv6 traffic, DNS, UDP/TCP, and unsolicited inbound traffic by default;
- prove an explicitly approved exact endpoint works only for the bound job, protocol, port, and lifetime;
- deny unapproved hostnames, direct IPs, private/link-local/loopback/reserved destinations, metadata/control-plane destinations, and alternate IP representations;
- deny DNS rebinding, mixed public/prohibited A/AAAA results, redirects, retries, and address-family fallback unless each destination is independently allowed;
- deny environment-configured proxies, alternate resolvers, encrypted-DNS endpoints, tunnels, and gateway-management access;
- prove one job's allow rule cannot be used by another job or tenant;
- prove policy-service/gateway failure, expiry, cancellation, and cleanup leave no residual egress;
- verify audit events and bounded failure reporting without leaking source code, credentials, or full payloads; and
- verify actual network routes and host/container configuration independently of the worker's own assertions.

Tests must verify both permitted and denied flows and retain failed attempts. A passing mock test or a diagram does not establish network isolation.

## 8. Observed repository state and completion status

Inspected `src/`, `pyproject.toml`, `docs/SECURITY_BOUNDARIES.md`, `docs/SECURITY_THREAT_MODEL.md`, `docs/SYSTEM_CONTEXT_AND_TRUST_BOUNDARIES.md`, and `docs/MODULAR_APPLICATION_BOUNDARIES.md`.

- The API is a health/diff-parsing shell and contains no sandbox or network policy.
- Architecture documents label the sandbox as planned/not implemented. `SECURITY_BOUNDARIES.md` requires a future isolated, resource-limited, network-restricted test/fix runner.
- No sandbox package, container/network policy, firewall rule set, network namespace controller, egress gateway, or network adversarial test suite was found in the inspected repository.
- No code, tests, build, or network probe was run for this milestone.

This document specifies intended behavior but cannot deny a packet. SEC-007 remains **TODO/partial** until a concrete sandbox enforcement boundary exists and adversarial network tests demonstrate default-deny behavior, explicit narrow allow behavior, DNS/IP restrictions, metadata blocking, and fail-closed cleanup. SEC-008 remains dependent on this work; repository execution is still prohibited pending sandbox security validation.
