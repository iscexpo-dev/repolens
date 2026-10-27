from __future__ import annotations

import pytest

from reviewforge.versioning import DEFAULT_COMPATIBILITY_POLICY, migrate_legacy_record


def test_current_versions_are_supported_for_each_component():
    for component in (
        "api",
        "finding",
        "prompt",
        "context_policy",
        "model_config",
        "dataset",
        "benchmark_manifest",
    ):
        assert DEFAULT_COMPATIBILITY_POLICY.validate(component, "1.0.0") == "1.0.0"


def test_unsupported_future_versions_are_rejected():
    with pytest.raises(ValueError, match="unsupported api version"):
        DEFAULT_COMPATIBILITY_POLICY.validate("api", "2.0.0")


def test_legacy_records_are_migrated_explicitly():
    payload = {"schema_version": "0.9.0", "run_id": "run-legacy", "reviewer": "fallback"}
    migrated = migrate_legacy_record("api", payload)

    assert migrated["schema_version"] == "1.0.0"
    assert migrated["compatibility_migration"] == {
        "component": "api",
        "from": "0.9.0",
        "to": "1.0.0",
        "reason": "explicit legacy migration",
    }
    assert migrated["reviewer"] == "fallback"


def test_unsupported_legacy_versions_fail_without_mutating_original_payload():
    payload = {"schema_version": "9.9.9", "run_id": "run-bad"}
    with pytest.raises(ValueError, match="unsupported api version"):
        migrate_legacy_record("api", payload)
    assert payload["schema_version"] == "9.9.9"


def test_component_policies_remain_separate_and_traceable():
    policy = DEFAULT_COMPATIBILITY_POLICY
    assert policy.for_component("api").description
    assert policy.for_component("benchmark_manifest").description
    assert policy.for_component("api").current_version == policy.for_component("finding").current_version == "1.0.0"
