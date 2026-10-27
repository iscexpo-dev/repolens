from datetime import datetime, timedelta, timezone

import pytest

from reviewforge.contracts import (
    SCHEMA_VERSION,
    BenchmarkRecord,
    BenchmarkStatus,
    CheckStatus,
    Finding,
    FindingEvidence,
    FindingStatus,
    PatchAttempt,
    PatchStatus,
    Policy,
    PolicyScope,
    PRSnapshot,
    ReviewBudget,
    ReviewRun,
    ReviewStatus,
    Severity,
    SnapshotFile,
    ToolResult,
)

NOW = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)
SHA256 = "a" * 64
COMMIT = "b" * 40


def test_all_required_domain_records_are_versioned_and_typed():
    snapshot = PRSnapshot(
        snapshot_id="snap-1",
        repository_id="org/repo",
        pull_request_number=7,
        base_commit_sha=COMMIT,
        head_commit_sha="c" * 40,
        diff_sha256=SHA256,
        acquired_at=NOW,
        files=(SnapshotFile("src/app.py", SHA256),),
    )
    evidence = FindingEvidence(
        evidence_ref="snapshot:snap-1",
        kind="source_location",
        path="src/app.py",
        line=12,
        changed_line_anchor=True,
        verified=True,
    )
    finding = Finding(
        finding_id="finding-1",
        review_run_id="run-1",
        snapshot_id=snapshot.snapshot_id,
        title="Invalid state transition",
        description="A retry can apply the operation twice.",
        impact="The user may be charged more than once.",
        recommendation="Make the operation idempotent.",
        category="reliability.idempotency",
        severity=Severity.HIGH,
        status=FindingStatus.VERIFIED,
        evidence=(evidence,),
        uncertainty="Reproduction was not run.",
    )
    policy = Policy(
        policy_id="policy-1",
        revision="rev-3",
        scope=PolicyScope.REPOSITORY,
        organization_id="org",
        repository_id="org/repo",
        categories=("correctness",),
        severities=(Severity.HIGH, Severity.CRITICAL),
        budget=ReviewBudget(max_cost_microusd=500_000, max_elapsed_seconds=90),
        excluded_paths=("vendor/generated",),
        required_checks=("static.diff",),
    )
    tool_result = ToolResult(
        result_id="tool-result-1",
        review_run_id="run-1",
        snapshot_id=snapshot.snapshot_id,
        tool_id="static.diff",
        tool_version="2.1",
        status=CheckStatus.COMPLETED,
        started_at=NOW,
        completed_at=NOW,
        finding_ids=(finding.finding_id,),
    )
    run = ReviewRun(
        run_id="run-1",
        snapshot_id=snapshot.snapshot_id,
        policy_id=policy.policy_id,
        policy_revision=policy.revision,
        configuration_digest=SHA256,
        status=ReviewStatus.COMPLETED,
        created_at=NOW,
        completed_at=NOW,
        finding_ids=(finding.finding_id,),
        tool_result_ids=(tool_result.result_id,),
    )
    patch = PatchAttempt(
        attempt_id="patch-1",
        finding_id=finding.finding_id,
        snapshot_id=snapshot.snapshot_id,
        status=PatchStatus.VERIFIED,
        created_at=NOW,
        patch_sha256=SHA256,
        authorized_by="user-1",
        completed_at=NOW,
        verification_result_ids=(tool_result.result_id,),
    )
    benchmark = BenchmarkRecord(
        record_id="bench-1",
        dataset_id="review-set",
        dataset_revision="rev-12",
        snapshot_id=snapshot.snapshot_id,
        configuration_digest=SHA256,
        status=BenchmarkStatus.COMPLETED,
        created_at=NOW,
        sample_count=1,
        provider_id="provider-x",
        provider_version="model-y-2026-10",
        prompt_digest=SHA256,
        tool_versions=("static.diff@2.1",),
        completed_at=NOW,
        metrics=(("precision", 1.0), ("recall", 0.5)),
    )

    records = (snapshot, finding, run, policy, tool_result, patch, benchmark)
    assert all(record.schema_version == SCHEMA_VERSION for record in records)
    assert all(record.__dataclass_params__.frozen for record in records)


def test_snapshot_rejects_invalid_commit_digest_time_and_path():
    with pytest.raises(ValueError, match="base_commit_sha"):
        PRSnapshot("s", "org/repo", 1, "not-a-commit", COMMIT, SHA256, NOW)

    with pytest.raises(ValueError, match="diff_sha256"):
        PRSnapshot("s", "org/repo", 1, COMMIT, COMMIT, "bad", NOW)

    with pytest.raises(ValueError, match="UTC"):
        PRSnapshot(
            "s",
            "org/repo",
            1,
            COMMIT,
            COMMIT,
            SHA256,
            datetime(2026, 10, 24, 8, 0),
        )

    with pytest.raises(ValueError, match="UTC"):
        PRSnapshot(
            "s",
            "org/repo",
            1,
            COMMIT,
            COMMIT,
            SHA256,
            datetime(2026, 10, 24, 8, 0, tzinfo=timezone(timedelta(hours=1))),
        )

    with pytest.raises(ValueError, match="repository-relative"):
        SnapshotFile("../outside.py", SHA256)


def test_version_and_finding_evidence_are_validated():
    with pytest.raises(ValueError, match="unsupported schema_version"):
        SnapshotFile("src/app.py", SHA256, schema_version="2.0.0")

    with pytest.raises(ValueError, match="changed-line anchor requires"):
        FindingEvidence(
            evidence_ref="source",
            kind="source_location",
            changed_line_anchor=True,
        )


def test_policy_preserves_inherit_and_explicit_empty_and_rejects_bad_scope():
    inherited = Policy("p", "r1", PolicyScope.ORGANIZATION, "org")
    disabled = Policy(
        "p2",
        "r1",
        PolicyScope.REPOSITORY,
        "org",
        repository_id="org/repo",
        categories=(),
        severities=(),
        excluded_paths=(),
        required_checks=(),
    )
    assert inherited.categories is None
    assert disabled.categories == ()
    assert disabled.severities == ()

    with pytest.raises(ValueError, match="requires.*repository_id"):
        Policy("p", "r1", PolicyScope.REPOSITORY, "org")

    with pytest.raises(ValueError, match="repository_id must be a non-empty string"):
        Policy("p2-empty", "r1", PolicyScope.REPOSITORY, "org", repository_id=" ")

    with pytest.raises(ValueError, match="severities entries must be unique"):
        Policy(
            "p3",
            "r1",
            PolicyScope.ORGANIZATION,
            "org",
            severities=(Severity.HIGH, Severity.HIGH),
        )

    with pytest.raises(ValueError, match="non-negative"):
        ReviewBudget(max_model_tokens=-1)


def test_results_require_consistent_terminal_evidence_and_utc_times():
    with pytest.raises(ValueError, match="completed tool result requires"):
        ToolResult(
            "t",
            "r",
            "s",
            "tool",
            "1",
            CheckStatus.COMPLETED,
            NOW,
        )

    with pytest.raises(ValueError, match="terminal review status requires"):
        ReviewRun("r", "s", "p", "rev1", SHA256, ReviewStatus.COMPLETED, NOW)

    with pytest.raises(ValueError, match="verified patch requires"):
        PatchAttempt(
            "a",
            "f",
            "s",
            PatchStatus.VERIFIED,
            NOW,
            patch_sha256=SHA256,
        )


def test_benchmark_record_rejects_invalid_digests_duplicate_metrics_and_count():
    with pytest.raises(ValueError, match="prompt_digest"):
        BenchmarkRecord(
            "b",
            "dataset",
            "r1",
            "snapshot",
            SHA256,
            BenchmarkStatus.PLANNED,
            NOW,
            0,
            prompt_digest="not-a-digest",
        )

    with pytest.raises(ValueError, match="metric names must be unique"):
        BenchmarkRecord(
            "b",
            "dataset",
            "r1",
            "snapshot",
            SHA256,
            BenchmarkStatus.PLANNED,
            NOW,
            0,
            metrics=(("precision", 0.7), ("precision", 0.8)),
        )

    with pytest.raises(ValueError, match="finite number"):
        BenchmarkRecord(
            "b",
            "dataset",
            "r1",
            "snapshot",
            SHA256,
            BenchmarkStatus.PLANNED,
            NOW,
            0,
            metrics=(("precision", float("nan")),),
        )

    with pytest.raises(ValueError, match="sample_count"):
        BenchmarkRecord(
            "b",
            "dataset",
            "r1",
            "snapshot",
            SHA256,
            BenchmarkStatus.PLANNED,
            NOW,
            -1,
        )
