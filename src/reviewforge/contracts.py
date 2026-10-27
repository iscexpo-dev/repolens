"""Versioned, dependency-free domain contracts for review data.

These schemas validate application-owned metadata, not provider payloads or
repository source. Callers must still authenticate, authorize, and validate
external payloads before constructing these immutable records. Evidence/status
flags are recorded assertions; they do not replace independent verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import math
import re
from typing import Final, Literal

SchemaVersion = Literal["1.0.0"]
SCHEMA_VERSION: Final[SchemaVersion] = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ReviewStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELED = "canceled"
    SUPERSEDED = "superseded"


class CheckStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    TIMED_OUT = "timed_out"


class FindingStatus(StrEnum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


class PolicyScope(StrEnum):
    ORGANIZATION = "organization"
    REPOSITORY = "repository"


class PatchStatus(StrEnum):
    PROPOSED = "proposed"
    AUTHORIZED = "authorized"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"
    VERIFIED = "verified"


class BenchmarkStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _version(value: str) -> None:
    if value != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {value!r}")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be a timezone-aware UTC datetime")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be UTC")


def _sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")


def _commit(value: str, field: str) -> None:
    if not isinstance(value, str) or not _COMMIT_RE.fullmatch(value):
        raise ValueError(f"{field} must be a 40- or 64-character lowercase commit ID")


def _relative_path(value: str, field: str) -> None:
    _nonempty(value, field)
    if value.startswith("/") or "\\" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"{field} must be a normalized repository-relative path")


def _enum(value: object, enum_type: type[StrEnum], field: str) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{field} must be a {enum_type.__name__}")


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    path: str
    content_sha256: str
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        _relative_path(self.path, "path")
        _sha256(self.content_sha256, "content_sha256")


@dataclass(frozen=True, slots=True)
class PRSnapshot:
    snapshot_id: str
    repository_id: str
    pull_request_number: int
    base_commit_sha: str
    head_commit_sha: str
    diff_sha256: str
    acquired_at: datetime
    merge_base_sha: str | None = None
    files: tuple[SnapshotFile, ...] = ()
    truncated: bool = False
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        _nonempty(self.snapshot_id, "snapshot_id")
        _nonempty(self.repository_id, "repository_id")
        if type(self.pull_request_number) is not int or self.pull_request_number < 1:
            raise ValueError("pull_request_number must be a positive integer")
        _commit(self.base_commit_sha, "base_commit_sha")
        _commit(self.head_commit_sha, "head_commit_sha")
        if self.merge_base_sha is not None:
            _commit(self.merge_base_sha, "merge_base_sha")
        _sha256(self.diff_sha256, "diff_sha256")
        _utc(self.acquired_at, "acquired_at")
        if not isinstance(self.files, tuple) or any(not isinstance(item, SnapshotFile) for item in self.files):
            raise ValueError("files must be a tuple of SnapshotFile records")
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("snapshot file paths must be unique")
        if type(self.truncated) is not bool:
            raise ValueError("truncated must be a bool")


@dataclass(frozen=True, slots=True)
class FindingEvidence:
    evidence_ref: str
    kind: str
    path: str | None = None
    line: int | None = None
    changed_line_anchor: bool = False
    verified: bool = False
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        _nonempty(self.evidence_ref, "evidence_ref")
        _nonempty(self.kind, "kind")
        if self.path is not None:
            _relative_path(self.path, "path")
        if self.line is not None and (type(self.line) is not int or self.line < 1):
            raise ValueError("line must be a positive integer when supplied")
        if self.changed_line_anchor and (self.path is None or self.line is None):
            raise ValueError("a changed-line anchor requires path and line")
        if type(self.changed_line_anchor) is not bool or type(self.verified) is not bool:
            raise ValueError("evidence flags must be bools")


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    review_run_id: str
    snapshot_id: str
    title: str
    description: str
    impact: str
    recommendation: str
    category: str
    severity: Severity
    status: FindingStatus
    evidence: tuple[FindingEvidence, ...]
    uncertainty: str
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("finding_id", "review_run_id", "snapshot_id", "title", "description",
                     "impact", "recommendation", "category", "uncertainty"):
            _nonempty(getattr(self, name), name)
        _enum(self.severity, Severity, "severity")
        _enum(self.status, FindingStatus, "status")
        if not isinstance(self.evidence, tuple) or any(not isinstance(item, FindingEvidence) for item in self.evidence):
            raise ValueError("evidence must be a tuple of FindingEvidence records")
        if self.status == FindingStatus.VERIFIED and not any(item.verified for item in self.evidence):
            raise ValueError("a verified finding requires verified evidence")


@dataclass(frozen=True, slots=True)
class ReviewBudget:
    max_cost_microusd: int | None = None
    max_elapsed_seconds: int | None = None
    max_model_tokens: int | None = None

    def __post_init__(self) -> None:
        for name in ("max_cost_microusd", "max_elapsed_seconds", "max_model_tokens"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or None")


@dataclass(frozen=True, slots=True)
class Policy:
    policy_id: str
    revision: str
    scope: PolicyScope
    organization_id: str
    repository_id: str | None = None
    categories: tuple[str, ...] | None = None
    severities: tuple[Severity, ...] | None = None
    budget: ReviewBudget | None = None
    excluded_paths: tuple[str, ...] | None = None
    required_checks: tuple[str, ...] | None = None
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("policy_id", "revision", "organization_id"):
            _nonempty(getattr(self, name), name)
        _enum(self.scope, PolicyScope, "scope")
        if self.scope == PolicyScope.REPOSITORY:
            if self.repository_id is None:
                raise ValueError("repository scope requires repository_id")
            _nonempty(self.repository_id, "repository_id")
        elif self.repository_id is not None:
            raise ValueError("organization-scoped policy cannot set repository_id")
        if self.categories is not None:
            _string_tuple(self.categories, "categories")
        if self.severities is not None:
            if not isinstance(self.severities, tuple):
                raise ValueError("severities must be a tuple or None (empty tuple disables all)")
            for severity in self.severities:
                _enum(severity, Severity, "severities item")
            if len(self.severities) != len(set(self.severities)):
                raise ValueError("severities entries must be unique")
        if self.budget is not None and not isinstance(self.budget, ReviewBudget):
            raise ValueError("budget must be ReviewBudget or None")
        if self.excluded_paths is not None:
            _string_tuple(self.excluded_paths, "excluded_paths")
            for path in self.excluded_paths:
                _relative_path(path, "excluded_paths item")
        if self.required_checks is not None:
            _string_tuple(self.required_checks, "required_checks")


def _string_tuple(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{field} must be a tuple or None")
    for item in values:
        _nonempty(item, f"{field} item")
    if len(values) != len(set(values)):
        raise ValueError(f"{field} entries must be unique")


@dataclass(frozen=True, slots=True)
class ToolResult:
    result_id: str
    review_run_id: str
    snapshot_id: str
    tool_id: str
    tool_version: str
    status: CheckStatus
    started_at: datetime
    completed_at: datetime | None = None
    finding_ids: tuple[str, ...] = ()
    artifact_sha256: tuple[str, ...] = ()
    error_code: str | None = None
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("result_id", "review_run_id", "snapshot_id", "tool_id", "tool_version"):
            _nonempty(getattr(self, name), name)
        _enum(self.status, CheckStatus, "status")
        _utc(self.started_at, "started_at")
        if self.completed_at is not None:
            _utc(self.completed_at, "completed_at")
            if self.completed_at < self.started_at:
                raise ValueError("completed_at cannot precede started_at")
        _string_tuple(self.finding_ids, "finding_ids")
        if not isinstance(self.artifact_sha256, tuple):
            raise ValueError("artifact_sha256 must be a tuple")
        for digest in self.artifact_sha256:
            _sha256(digest, "artifact_sha256 item")
        if self.error_code is not None:
            _nonempty(self.error_code, "error_code")
        if self.status == CheckStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed tool result requires completed_at")


@dataclass(frozen=True, slots=True)
class ReviewRun:
    run_id: str
    snapshot_id: str
    policy_id: str
    policy_revision: str
    configuration_digest: str
    status: ReviewStatus
    created_at: datetime
    completed_at: datetime | None = None
    finding_ids: tuple[str, ...] = ()
    tool_result_ids: tuple[str, ...] = ()
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("run_id", "snapshot_id", "policy_id", "policy_revision"):
            _nonempty(getattr(self, name), name)
        _sha256(self.configuration_digest, "configuration_digest")
        _enum(self.status, ReviewStatus, "status")
        _utc(self.created_at, "created_at")
        if self.completed_at is not None:
            _utc(self.completed_at, "completed_at")
            if self.completed_at < self.created_at:
                raise ValueError("completed_at cannot precede created_at")
        _string_tuple(self.finding_ids, "finding_ids")
        _string_tuple(self.tool_result_ids, "tool_result_ids")
        if self.status in {ReviewStatus.COMPLETED, ReviewStatus.PARTIAL, ReviewStatus.FAILED,
                           ReviewStatus.CANCELED, ReviewStatus.SUPERSEDED} and self.completed_at is None:
            raise ValueError("terminal review status requires completed_at")


@dataclass(frozen=True, slots=True)
class PatchAttempt:
    attempt_id: str
    finding_id: str
    snapshot_id: str
    status: PatchStatus
    created_at: datetime
    patch_sha256: str | None = None
    authorized_by: str | None = None
    completed_at: datetime | None = None
    verification_result_ids: tuple[str, ...] = ()
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("attempt_id", "finding_id", "snapshot_id"):
            _nonempty(getattr(self, name), name)
        _enum(self.status, PatchStatus, "status")
        _utc(self.created_at, "created_at")
        if self.patch_sha256 is not None:
            _sha256(self.patch_sha256, "patch_sha256")
        if self.authorized_by is not None:
            _nonempty(self.authorized_by, "authorized_by")
        if self.completed_at is not None:
            _utc(self.completed_at, "completed_at")
            if self.completed_at < self.created_at:
                raise ValueError("completed_at cannot precede created_at")
        _string_tuple(self.verification_result_ids, "verification_result_ids")
        if self.status in {PatchStatus.APPLIED, PatchStatus.VERIFIED} and self.patch_sha256 is None:
            raise ValueError("applied or verified patch requires patch_sha256")
        if self.status == PatchStatus.VERIFIED and not self.verification_result_ids:
            raise ValueError("verified patch requires verification result IDs")


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    record_id: str
    dataset_id: str
    dataset_revision: str
    snapshot_id: str
    configuration_digest: str
    status: BenchmarkStatus
    created_at: datetime
    sample_count: int
    provider_id: str | None = None
    provider_version: str | None = None
    prompt_digest: str | None = None
    tool_versions: tuple[str, ...] = ()
    completed_at: datetime | None = None
    metrics: tuple[tuple[str, float], ...] = ()
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in ("record_id", "dataset_id", "dataset_revision", "snapshot_id"):
            _nonempty(getattr(self, name), name)
        _sha256(self.configuration_digest, "configuration_digest")
        _enum(self.status, BenchmarkStatus, "status")
        _utc(self.created_at, "created_at")
        if type(self.sample_count) is not int or self.sample_count < 0:
            raise ValueError("sample_count must be a non-negative integer")
        for name in ("provider_id", "provider_version"):
            value = getattr(self, name)
            if value is not None:
                _nonempty(value, name)
        if self.prompt_digest is not None:
            _sha256(self.prompt_digest, "prompt_digest")
        _string_tuple(self.tool_versions, "tool_versions")
        if self.completed_at is not None:
            _utc(self.completed_at, "completed_at")
            if self.completed_at < self.created_at:
                raise ValueError("completed_at cannot precede created_at")
        if not isinstance(self.metrics, tuple):
            raise ValueError("metrics must be a tuple of (name, value) pairs")
        names: list[str] = []
        for item in self.metrics:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError("each metric must be a (name, value) tuple")
            name, value = item
            _nonempty(name, "metric name")
            if type(value) not in {int, float} or not math.isfinite(value):
                raise ValueError("metric value must be a finite number")
            names.append(name)
        if len(names) != len(set(names)):
            raise ValueError("metric names must be unique")
        if self.status == BenchmarkStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed benchmark record requires completed_at")
