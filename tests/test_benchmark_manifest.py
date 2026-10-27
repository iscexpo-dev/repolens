from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from reviewforge.benchmark.manifest import (
    ArtifactReference,
    BenchmarkRunManifest,
    CommitSnapshot,
    DatasetRevision,
    EnvironmentIdentity,
    ReviewerConfig,
    RunBudget,
    RunStatus,
    ToolVersion,
)


UTC = timezone.utc
CREATED = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
BASE = "1" * 40
HEAD = "2" * 40


def make_manifest(**changes):
    values = {
        "run_id": "run-2026-001",
        "created_at": CREATED,
        "protocol_id": "repolens-review-benchmark",
        "protocol_version": "1.0.0",
        "protocol_sha256": HASH_A,
        "dataset": DatasetRevision("synthetic-fixture", "rev-7", HASH_A),
        "snapshots": (CommitSnapshot("example/repo", BASE, HEAD, HASH_B, HASH_C),),
        "reviewer": ReviewerConfig("offline-test", "model-fixture-v1", HASH_A, HASH_B),
        "tools": (ToolVersion("reviewer", "0.1.0"),),
        "budget": RunBudget(60, 1000, 500, 250000),
        "environment": EnvironmentIdentity("test-os", "test-arch", "python-3.11", HASH_C),
    }
    values.update(changes)
    return BenchmarkRunManifest(**values)


def result_artifact():
    return ArtifactReference("raw-results", "artifact://synthetic/results.json", HASH_A, 12, "application/json")


def test_manifest_is_versioned_canonical_and_digest_round_trips():
    manifest = make_manifest()
    decoded = BenchmarkRunManifest.from_json(manifest.to_json())

    assert manifest.schema_version == "1.0.0"
    assert manifest.canonical_bytes() == decoded.canonical_bytes()
    assert manifest.digest_sha256 == decoded.digest_sha256
    assert manifest.digest_sha256 == BenchmarkRunManifest.from_dict(manifest.to_dict()).digest_sha256
    assert manifest.to_json() == decoded.to_json()


def test_same_semantics_have_same_canonical_digest_independent_of_input_key_order():
    manifest = make_manifest()
    obj = manifest.to_dict()
    reordered = dict(reversed(list(obj.items())))

    assert BenchmarkRunManifest.from_dict(reordered).canonical_bytes() == manifest.canonical_bytes()
    assert BenchmarkRunManifest.from_dict(reordered).digest_sha256 == manifest.digest_sha256


def test_digest_detects_modified_content_and_untrusted_digest():
    altered = make_manifest().to_dict()
    altered["protocol_id"] = "altered-protocol"
    with pytest.raises(ValueError, match="digest mismatch"):
        BenchmarkRunManifest.from_dict(altered)

    altered = make_manifest().to_dict()
    altered["digest_sha256"] = HASH_B
    with pytest.raises(ValueError, match="digest mismatch"):
        BenchmarkRunManifest.from_dict(altered)


def test_unknown_missing_and_duplicate_json_keys_are_rejected():
    obj = make_manifest().to_dict()
    obj["unrecognized"] = True
    with pytest.raises(ValueError, match="keys mismatch"):
        BenchmarkRunManifest.from_dict(obj)

    obj = make_manifest().to_dict()
    del obj["dataset"]
    with pytest.raises(ValueError, match="keys mismatch"):
        BenchmarkRunManifest.from_dict(obj)

    with pytest.raises(ValueError, match="duplicate JSON key"):
        BenchmarkRunManifest.from_json("{\"x\":1,\"x\":2}")


def test_unsupported_schema_and_nonfinite_json_are_rejected():
    obj = make_manifest().to_dict()
    obj["schema_version"] = "2.0.0"
    with pytest.raises(ValueError, match="unsupported schema_version"):
        BenchmarkRunManifest.from_dict(obj)
    with pytest.raises(ValueError, match="non-finite JSON number"):
        BenchmarkRunManifest.from_json("NaN")


def test_required_hashes_commit_ids_versions_and_budget_types_are_strict():
    with pytest.raises(ValueError, match="manifest_sha256"):
        DatasetRevision("dataset", "revision", "bad")
    with pytest.raises(ValueError, match="commit ID"):
        CommitSnapshot("repo", "bad", HEAD, HASH_A, HASH_B)
    with pytest.raises(ValueError, match="must differ"):
        CommitSnapshot("repo", BASE, BASE, HASH_A, HASH_B)
    with pytest.raises(ValueError, match="positive integer"):
        RunBudget(True, 10, 10, 10)
    with pytest.raises(ValueError, match="semantic version"):
        make_manifest(protocol_version="release-latest")
    with pytest.raises(ValueError, match="protocol_sha256"):
        make_manifest(protocol_sha256="bad")


def test_manifest_rejects_duplicate_repositories_tools_and_artifact_names():
    snapshot = CommitSnapshot("example/repo", "3" * 40, "4" * 40, HASH_A, HASH_B)
    with pytest.raises(ValueError, match="repository_id values must be unique"):
        make_manifest(snapshots=(make_manifest().snapshots[0], snapshot))
    with pytest.raises(ValueError, match="non-empty tuple"):
        make_manifest(tools=())
    with pytest.raises(ValueError, match="tool names must be unique"):
        make_manifest(tools=(ToolVersion("tool", "1"), ToolVersion("tool", "2")))
    artifact = result_artifact()
    running = make_manifest(status=RunStatus.RUNNING, started_at=CREATED + timedelta(seconds=1))
    with pytest.raises(ValueError, match="artifact names must be unique"):
        replace(running, status=RunStatus.COMPLETED, finished_at=CREATED + timedelta(seconds=2), artifacts=(artifact, artifact))


def test_state_machine_accepts_complete_run_and_keeps_inputs_immutable():
    planned = make_manifest()
    running = planned.transition(RunStatus.RUNNING, CREATED + timedelta(seconds=1))
    completed = running.transition(RunStatus.COMPLETED, CREATED + timedelta(seconds=5), artifacts=(result_artifact(),))

    assert planned.status is RunStatus.PLANNED and planned.started_at is None
    assert running.status is RunStatus.RUNNING and running.finished_at is None
    assert completed.status is RunStatus.COMPLETED and completed.finished_at == CREATED + timedelta(seconds=5)
    assert BenchmarkRunManifest.from_json(completed.to_json()) == completed


def test_state_machine_rejects_skipped_reversed_and_terminal_transitions():
    planned = make_manifest()
    with pytest.raises(ValueError, match="invalid run-state transition"):
        planned.transition(RunStatus.COMPLETED, CREATED + timedelta(seconds=3), artifacts=(result_artifact(),))
    with pytest.raises(ValueError, match="starting requires"):
        planned.transition(RunStatus.RUNNING, CREATED - timedelta(seconds=1))

    running = planned.transition(RunStatus.RUNNING, CREATED + timedelta(seconds=1))
    with pytest.raises(ValueError, match="terminal transition"):
        running.transition(RunStatus.COMPLETED, CREATED, artifacts=(result_artifact(),))
    completed = running.transition(RunStatus.COMPLETED, CREATED + timedelta(seconds=2), artifacts=(result_artifact(),))
    with pytest.raises(ValueError, match="invalid run-state transition"):
        completed.transition(RunStatus.RUNNING, CREATED + timedelta(seconds=3))


def test_partial_failed_and_cancelled_states_enforce_semantics():
    running = make_manifest().transition(RunStatus.RUNNING, CREATED + timedelta(seconds=1))
    with pytest.raises(ValueError, match="partial run requires"):
        running.transition(RunStatus.PARTIAL, CREATED + timedelta(seconds=2))
    partial = running.transition(RunStatus.PARTIAL, CREATED + timedelta(seconds=2), artifacts=(result_artifact(),), failure_reason="one task timed out")
    assert partial.status is RunStatus.PARTIAL
    failed = running.transition(RunStatus.FAILED, CREATED + timedelta(seconds=2), failure_reason="worker failed")
    assert failed.status is RunStatus.FAILED
    cancelled = make_manifest().transition(RunStatus.CANCELLED, CREATED + timedelta(seconds=1))
    assert cancelled.status is RunStatus.CANCELLED and cancelled.started_at is None
    with pytest.raises(ValueError, match="invalid run-state transition"):
        cancelled.transition(RunStatus.RUNNING, CREATED + timedelta(seconds=2))


def test_completed_manifest_requires_result_artifact_and_terminal_time():
    with pytest.raises(ValueError, match="completed run requires"):
        make_manifest(status=RunStatus.COMPLETED, started_at=CREATED, finished_at=CREATED + timedelta(seconds=1))
    with pytest.raises(ValueError, match="finished_at cannot precede"):
        make_manifest(status=RunStatus.RUNNING, started_at=CREATED + timedelta(seconds=1), finished_at=CREATED)


def test_naive_and_non_utc_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        make_manifest(created_at=datetime(2026, 10, 24))
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        make_manifest(created_at=CREATED.astimezone(timezone(timedelta(hours=2))))


def test_atomic_local_file_round_trip_uses_temporary_fixture(tmp_path):
    destination = tmp_path / "run-manifest.json"
    manifest = make_manifest()
    manifest.write(destination)

    assert BenchmarkRunManifest.read(destination) == manifest
    assert json.loads(destination.read_text(encoding="utf-8"))["digest_sha256"] == manifest.digest_sha256


def test_artifact_integrity_reference_rejects_invalid_hash_and_negative_size():
    with pytest.raises(ValueError, match="SHA-256"):
        ArtifactReference("output", "artifact://local/output", "bad", 0, "application/json")
    with pytest.raises(ValueError, match="non-negative integer"):
        ArtifactReference("output", "artifact://local/output", HASH_A, -1, "application/json")


def test_artifact_reference_requires_absolute_credential_free_uri_and_known_kind():
    with pytest.raises(ValueError, match="supported absolute URI"):
        ArtifactReference("output", "relative/path", HASH_A, 0, "application/json")
    with pytest.raises(ValueError, match="without credentials"):
        ArtifactReference("output", "https://@example.invalid/results", HASH_A, 0, "application/json")
    with pytest.raises(ValueError, match="supported artifact classification"):
        ArtifactReference("output", "artifact://local/output", HASH_A, 0, "application/json", kind="unknown")


def test_artifact_reference_rejects_query_and_fragment_data():
    with pytest.raises(ValueError, match="without credentials, query, or fragment"):
        ArtifactReference("output", "https://example.invalid/results?x=1", HASH_A, 0, "application/json")
    with pytest.raises(ValueError, match="without credentials, query, or fragment"):
        ArtifactReference("output", "https://example.invalid/results#fragment", HASH_A, 0, "application/json")
