# SEC-007 Acceptance Test Matrix

**State:** Test design only; none of these network tests has run. Run these
against the selected, real host/platform enforcement boundary from disposable,
resource-limited jobs with no developer or production credentials. Mocks,
source inspection, a policy document, or host-level connectivity checks are
not passing evidence. Record runtime/image and policy revisions, job identity,
test harness and destination ownership, timestamps, worker and gateway
logs, packet/flow evidence, cleanup result, and reviewer for each case.

| ID | Threat / required setup | Harness and expected result | Independent evidence / pass criterion |
|---|---|---|---|
| E01 | Default egress; fresh job, no exceptions | Attempt outbound TCP, UDP, ICMP, and DNS on IPv4 and IPv6. Every attempt is denied; job has no alternate route. | From inside job, capture failed attempts; platform route/firewall and gateway logs show default deny for that job. Any successful path fails. |
| E02 | Exception overreach; trusted controller provisions one exact test service, port, and protocol | Connect to the approved endpoint; it succeeds only for the approved job, destination, port, protocol, and validity interval. Neighbor destinations/ports remain denied. | Independent gateway/firewall decision log matches the approved policy revision and job; unintended success fails. |
| E03 | Unauthorized TCP and UDP; use controlled test endpoints | Probe authorized and unauthorized ports/protocols, including UDP and non-HTTP traffic. Only explicitly authorized flows succeed. | Worker-side attempts plus external endpoint and enforcement logs corroborate every expected allow/deny; any unapproved connection fails. |
| E04 | DNS and alternate resolvers; controlled resolver endpoints | Query the configured resolver, direct-IP resolvers, alternate ports, DNS-over-HTTPS/TLS, and a controlled rebinding name. Default job cannot resolve externally or tunnel DNS; approved hostname resolution is policy-mediated and pinned/revalidated. | Resolver and gateway logs show denied alternate paths and approved query/address binding; successful bypass or connection to a prohibited rebinding result fails. |
| E05 | IPv4/IPv6 and hostname/direct-IP bypasses; controlled public test endpoints and prohibited test ranges | Attempt each family by hostname and literal address, including mapped/normalized forms. Only approved addresses pass; internal, loopback, link-local, reserved and unapproved destinations fail. | Packet/flow evidence and external policy decision logs cover both families and actual connected addresses; any uncovered family/path or prohibited success fails. |
| E06 | Redirect and proxy bypass; controlled redirector/proxy/tunnel endpoints | Approved service redirects to an unapproved target; attempt inherited proxy variables, direct proxy, CONNECT, VPN/tunnel, and alternate interfaces. Each target is reauthorized or denied; no bypass succeeds. | Gateway/worker logs show redirect reauthorization and denied alternate path; unauthorized destination success fails. |
| E07 | Metadata/internal/control-plane access; environment-specific destinations inventoried by the platform owner | From job, attempt known metadata/identity, node/cluster/control-plane, host management, private/internal service, and gateway-management destinations over supported protocols and IP families. All are denied. | Platform owner supplies current destination/routing inventory; independent flow logs show denies. Any response containing metadata, credentials, or control-plane data fails. |
| E08 | Host and neighboring job access; two simultaneous jobs plus controlled host/service sentinels | Attempt host gateway/socket/services, peer job addresses, shared mounts, and service discovery from each job. No cross-job or host access succeeds. | Separate job IDs, route/namespace configuration, sentinel logs, and denied flow evidence establish separation; any cross-access fails. |
| E09 | Per-job identity and policy isolation; two jobs with different explicit policies | Grant one job a narrow exception; repeat the same request from the other job. Only the authorized job succeeds. | Controller, gateway, and both job logs bind decisions to distinct identities and revisions; policy leakage fails. |
| E10 | Revocation and runtime update; active job with expiring test exception | Revoke or narrow the exception while job runs; new connections and reconnects are denied within the approved revocation bound. Existing-flow behavior is explicitly measured and meets the platform-approved cutoff. | Timestamped controller/gateway decisions verify policy revision propagation and cutoff; stale permission beyond the bound fails. |
| E11 | Initialization/policy installation failure; inject controlled controller/gateway errors | Force policy retrieval, namespace/rule install, DNS setup, or health-check failure. Scheduler refuses to start untrusted commands and reports a bounded failure. | Orchestrator state plus worker process/audit evidence shows no command started; any execution before enforcement is installed fails. |
| E12 | Gateway/firewall failure; controlled test failure, not shared infrastructure | Simulate loss or stale health of the isolated test gateway/policy service. Traffic remains denied and jobs stop or fail according to policy; no fail-open route appears. | Fault-injection record, routes, worker attempts, and independent gateway/controller health logs; any successful egress during failure fails. |
| E13 | Cancellation/termination/cleanup; disposable job | Cancel and forcibly terminate jobs during setup, active allowed flow, and teardown. Revoke policy, terminate processes, remove namespace/routes/storage, and prevent stale job identity reuse. | Lifecycle/audit events and post-cleanup route/process/identity checks show cleanup completed within the approved bound; surviving access fails. |
| E14 | Secrets in environment, mounted files, logs, subprocesses; use synthetic canary values only | Verify no credentials are injected or mounted; attempt to read synthetic canaries through process/environment/log paths and emit them to a controlled denied endpoint. | Controller configuration, mount inventory, sanitized logs, canary scan, and denied flow records show no secret exposure; any real secret or canary egress fails. |
| E15 | Audit integrity and policy change; trusted administrator changes an exception | Create, approve, activate, revoke, and expire a test policy. Each event is attributable, time-ordered, job-bound, and source/secret-free; worker cannot modify the record. | Access-controlled append-only audit records reconcile with controller/gateway actions; missing, mutable, or unbound events fail. |

## Preconditions and test record

Before execution, the authorized platform owner must document the runtime,
network topology, DNS path, IPv4/IPv6 support, prohibited ranges and
environment-specific metadata/control-plane destinations, approved egress
model, policy propagation/revocation bounds, required privileges, and
disposable test endpoints. Security review must approve the harness and
failure-injection scope.

For every case record: `test_id`, pass/fail/not-run, environment and runtime
versions, worker/job/policy identities, exact safe harness invocation,
expected and observed outcome, independent artifacts, timestamps, cleanup,
deviation, reviewer, and linked issue. A test is **PASS** only when both the
job-side outcome and independent enforcement evidence agree. Mark cases
**NOT RUN** or **INSUFFICIENT EVIDENCE** when the required boundary or
independent artifacts are absent. SEC-007 stays blocked until every mandatory
case is executed successfully and independently reviewed.
