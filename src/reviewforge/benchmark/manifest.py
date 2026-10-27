"""Typed, versioned and integrity-checked benchmark run manifests.

The manifest records reproducibility metadata; it neither fetches artifacts nor
proves the authenticity of a digest. All inputs are application-owned metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from typing import Final, Literal, TypeAlias

SCHEMA_VERSION: Final = "1.0.0"
SchemaVersion: TypeAlias = Literal["1.0.0"]
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


class RunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _sha(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def _commit(value: object, name: str) -> None:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase 40- or 64-character commit ID")


def _utc(value: object, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be a timezone-aware UTC datetime")


def _positive_int(value: object, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _version(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or not _SEMVER.fullmatch(value):
        raise ValueError(f"{name} must be a semantic version")


def _datetime_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    _utc(value, "timestamp")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{name} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid ISO-8601 UTC timestamp") from exc
    _utc(parsed, name)
    return parsed


def _exact_keys(data: object, expected: set[str], name: str) -> dict[str, object]:
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise ValueError(f"{name} must be an object with string keys")
    missing = expected - data.keys()
    extra = data.keys() - expected
    if missing or extra:
        raise ValueError(f"{name} keys mismatch; missing={sorted(missing)}, unknown={sorted(extra)}")
    return data


def _duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


@dataclass(frozen=True, slots=True)
class DatasetRevision:
    dataset_id: str
    revision: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        _text(self.dataset_id, "dataset_id")
        _text(self.revision, "dataset.revision")
        _sha(self.manifest_sha256, "dataset.manifest_sha256")

    def to_dict(self) -> dict[str, object]:
        return {"dataset_id": self.dataset_id, "revision": self.revision, "manifest_sha256": self.manifest_sha256}

    @classmethod
    def from_dict(cls, data: object) -> DatasetRevision:
        obj = _exact_keys(data, {"dataset_id", "revision", "manifest_sha256"}, "dataset")
        return cls(obj["dataset_id"], obj["revision"], obj["manifest_sha256"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class CommitSnapshot:
    repository_id: str
    base_commit_sha: str
    head_commit_sha: str
    snapshot_sha256: str
    diff_sha256: str

    def __post_init__(self) -> None:
        _text(self.repository_id, "repository_id")
        _commit(self.base_commit_sha, "base_commit_sha")
        _commit(self.head_commit_sha, "head_commit_sha")
        _sha(self.snapshot_sha256, "snapshot_sha256")
        _sha(self.diff_sha256, "diff_sha256")
        if self.base_commit_sha == self.head_commit_sha:
            raise ValueError("base_commit_sha and head_commit_sha must differ")

    def to_dict(self) -> dict[str, str]:
        return {"repository_id": self.repository_id, "base_commit_sha": self.base_commit_sha,"head_commit_sha": self.head_commit_sha, "snapshot_sha256": self.snapshot_sha256, "diff_sha256": self.diff_sha256}

    @classmethod
    def from_dict(cls, data: object) -> CommitSnapshot:
        obj = _exact_keys(data, {"repository_id", "base_commit_sha", "head_commit_sha", "snapshot_sha256", "diff_sha256"}, "snapshot")
        return cls(obj["repository_id"], obj["base_commit_sha"], obj["head_commit_sha"], obj["snapshot_sha256"], obj["diff_sha256"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class ReviewerConfig:
    provider: str
    model_version: str
    prompt_sha256: str
    config_sha256: str

    def __post_init__(self) -> None:
        _text(self.provider, "provider")
        _text(self.model_version, "model_version")
        _sha(self.prompt_sha256, "prompt_sha256")
        _sha(self.config_sha256, "config_sha256")

    def to_dict(self) -> dict[str, str]:
        return {"provider": self.provider, "model_version": self.model_version,"prompt_sha256": self.prompt_sha256, "config_sha256": self.config_sha256}

    @classmethod
    def from_dict(cls, data: object) -> ReviewerConfig:
        obj = _exact_keys(data, {"provider", "model_version", "prompt_sha256", "config_sha256"}, "reviewer")
        return cls(obj["provider"], obj["model_version"], obj["prompt_sha256"], obj["config_sha256"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class ToolVersion:
    name: str
    version: str

    def __post_init__(self) -> None:
        _text(self.name, "tool.name")
        _text(self.version, "tool.version")

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version}

    @classmethod
    def from_dict(cls, data: object) -> ToolVersion:
        obj = _exact_keys(data, {"name", "version"}, "tool")
        return cls(obj["name"], obj["version"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class RunBudget:
    max_runtime_seconds: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_microusd: int

    def __post_init__(self) -> None:
        for name in ("max_runtime_seconds", "max_input_tokens", "max_output_tokens", "max_cost_microusd"):
            _positive_int(getattr(self, name), name)

    def to_dict(self) -> dict[str, int]:
        return {"max_runtime_seconds": self.max_runtime_seconds, "max_input_tokens": self.max_input_tokens,"max_output_tokens": self.max_output_tokens, "max_cost_microusd": self.max_cost_microusd}

    @classmethod
    def from_dict(cls, data: object) -> RunBudget:
        obj = _exact_keys(data, {"max_runtime_seconds", "max_input_tokens", "max_output_tokens", "max_cost_microusd"}, "budget")
        return cls(obj["max_runtime_seconds"], obj["max_input_tokens"], obj["max_output_tokens"], obj["max_cost_microusd"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class EnvironmentIdentity:
    operating_system: str
    architecture: str
    runtime_version: str
    environment_sha256: str

    def __post_init__(self) -> None:
        for name in ("operating_system", "architecture", "runtime_version"):
            _text(getattr(self, name), name)
        _sha(self.environment_sha256, "environment_sha256")

    def to_dict(self) -> dict[str, str]:
        return {"operating_system": self.operating_system, "architecture": self.architecture,"runtime_version": self.runtime_version, "environment_sha256": self.environment_sha256}

    @classmethod
    def from_dict(cls, data: object) -> EnvironmentIdentity:
        obj = _exact_keys(data, {"operating_system", "architecture", "runtime_version", "environment_sha256"}, "environment")
        return cls(obj["operating_system"], obj["architecture"], obj["runtime_version"], obj["environment_sha256"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    name: str
    uri: str
    sha256: str
    size_bytes: int
    media_type: str
    kind: str = "result"

    def __post_init__(self) -> None:
        for name in ("name", "uri", "media_type", "kind"):
            _text(getattr(self, name), f"artifact.{name}")
        parsed_uri = urlsplit(self.uri)
        if (parsed_uri.scheme not in {"https", "s3", "file", "artifact"} or parsed_uri.username is not None or parsed_uri.password is not None or parsed_uri.query or parsed_uri.fragment or not (parsed_uri.netloc or parsed_uri.path)):
            raise ValueError("artifact.uri must be a supported absolute URI without credentials, query, or fragment")
        if self.kind not in {"result", "raw_output", "metrics", "logs", "uncertainty", "other"}:
            raise ValueError("artifact.kind must be a supported artifact classification")
        _sha(self.sha256, "artifact.sha256")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("artifact.size_bytes must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "uri": self.uri, "sha256": self.sha256,"size_bytes": self.size_bytes, "media_type": self.media_type, "kind": self.kind}

    @classmethod
    def from_dict(cls, data: object) -> ArtifactReference:
        obj = _exact_keys(data, {"name", "uri", "sha256", "size_bytes", "media_type", "kind"}, "artifact")
        return cls(obj["name"], obj["uri"], obj["sha256"], obj["size_bytes"], obj["media_type"], obj["kind"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class BenchmarkRunManifest:
    run_id: str
    created_at: datetime
    protocol_id: str
    protocol_version: str
    protocol_sha256: str
    dataset: DatasetRevision
    snapshots: tuple[CommitSnapshot, ...]
    reviewer: ReviewerConfig
    tools: tuple[ToolVersion, ...]
    budget: RunBudget
    environment: EnvironmentIdentity
    status: RunStatus = RunStatus.PLANNED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    artifacts: tuple[ArtifactReference, ...] = ()
    failure_reason: str | None = None
    schema_version: SchemaVersion = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _text(self.run_id, "run_id")
        _utc(self.created_at, "created_at")
        _text(self.protocol_id, "protocol_id")
        _version(self.protocol_version, "protocol_version")
        _sha(self.protocol_sha256, "protocol_sha256")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version!r}")
        if not isinstance(self.dataset, DatasetRevision) or not isinstance(self.reviewer, ReviewerConfig) or not isinstance(self.budget, RunBudget) or not isinstance(self.environment, EnvironmentIdentity):
            raise ValueError("dataset, reviewer, budget, and environment must use their typed records")
        if not isinstance(self.snapshots, tuple) or not self.snapshots or any(not isinstance(x, CommitSnapshot) for x in self.snapshots):
            raise ValueError("snapshots must be a non-empty tuple of CommitSnapshot records")
        repos = [x.repository_id for x in self.snapshots]
        if len(repos) != len(set(repos)):
            raise ValueError("snapshot repository_id values must be unique")
        if not isinstance(self.tools, tuple) or not self.tools or any(not isinstance(x, ToolVersion) for x in self.tools):
            raise ValueError("tools must be a non-empty tuple of ToolVersion records")
        tool_names = [x.name for x in self.tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError("tool names must be unique")
        if not isinstance(self.artifacts, tuple) or any(not isinstance(x, ArtifactReference) for x in self.artifacts):
            raise ValueError("artifacts must be a tuple of ArtifactReference records")
        artifact_names = [x.name for x in self.artifacts]
        if len(artifact_names) != len(set(artifact_names)):
            raise ValueError("artifact names must be unique")
        if not isinstance(self.status, RunStatus):
            raise ValueError("status must be a RunStatus")
        _utc(self.started_at, "started_at") if self.started_at is not None else None
        _utc(self.finished_at, "finished_at") if self.finished_at is not None else None
        if self.created_at > (self.started_at or self.created_at):
            raise ValueError("started_at cannot precede created_at")
        if self.finished_at is not None:
            if self.started_at is None and self.status != RunStatus.CANCELLED:
                raise ValueError("finished_at requires started_at except for a pre-start cancellation")
            if self.started_at is not None and self.finished_at < self.started_at:
                raise ValueError("finished_at cannot precede started_at")
        if self.failure_reason is not None:
            _text(self.failure_reason, "failure_reason")
        result_artifacts = [x for x in self.artifacts if x.kind == "result"]
        if self.status == RunStatus.PLANNED:
            if self.started_at is not None or self.finished_at is not None or self.artifacts or self.failure_reason is not None:
                raise ValueError("planned run cannot have lifecycle timestamps, artifacts, or failure_reason")
        elif self.status == RunStatus.RUNNING:
            if self.started_at is None or self.finished_at is not None or self.artifacts or self.failure_reason is not None:
                raise ValueError("running run requires started_at and cannot have terminal fields")
        elif self.status == RunStatus.COMPLETED:
            if self.started_at is None or self.finished_at is None or not result_artifacts or self.failure_reason is not None:
                raise ValueError("completed run requires lifecycle timestamps and a result artifact, without failure_reason")
        elif self.status == RunStatus.PARTIAL:
            if self.started_at is None or self.finished_at is None or not result_artifacts or self.failure_reason is None:
                raise ValueError("partial run requires lifecycle timestamps, a result artifact, and failure_reason")
        elif self.status == RunStatus.FAILED:
            if self.started_at is None or self.finished_at is None or self.failure_reason is None:
                raise ValueError("failed run requires lifecycle timestamps and failure_reason")
        elif self.status == RunStatus.CANCELLED:
            if self.finished_at is None or self.artifacts or self.failure_reason is not None:
                raise ValueError("cancelled run requires finished_at and cannot contain artifacts")
            if self.started_at is None and self.finished_at < self.created_at:
                raise ValueError("cancelled run cannot finish before creation")

    def _payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "run_id": self.run_id,"created_at": _datetime_to_text(self.created_at), "protocol_id": self.protocol_id,"protocol_version": self.protocol_version, "protocol_sha256": self.protocol_sha256, "dataset": self.dataset.to_dict(),"snapshots": [x.to_dict() for x in self.snapshots], "reviewer": self.reviewer.to_dict(),"tools": [x.to_dict() for x in self.tools], "budget": self.budget.to_dict(),"environment": self.environment.to_dict(), "status": self.status.value,"started_at": _datetime_to_text(self.started_at), "finished_at": _datetime_to_text(self.finished_at),"artifacts": [x.to_dict() for x in self.artifacts], "failure_reason": self.failure_reason}

    @property
    def digest_sha256(self) -> str:
        canonical = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"),ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def canonical_bytes(self) -> bytes:
        """Canonical UTF-8 JSON bytes excluding the digest field itself."""
        return json.dumps(self._payload(), sort_keys=True, separators=(",", ":"),ensure_ascii=False, allow_nan=False).encode("utf-8")

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "digest_sha256": self.digest_sha256}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"),ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, data: object) -> BenchmarkRunManifest:
        keys = {"schema_version", "run_id", "created_at", "protocol_id","protocol_version", "protocol_sha256", "dataset", "snapshots", "reviewer","tools", "budget", "environment", "status", "started_at","finished_at", "artifacts", "failure_reason", "digest_sha256"}
        obj = _exact_keys(data, keys, "manifest")
        if obj["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {obj["schema_version"]!r}")
        try:
            status = RunStatus(obj["status"])
        except (ValueError, TypeError) as exc:
            raise ValueError("status must be a supported run state") from exc
        if not isinstance(obj["snapshots"], list) or not isinstance(obj["tools"], list) or not isinstance(obj["artifacts"], list):
            raise ValueError("snapshots, tools, and artifacts must be arrays")
        reason = obj["failure_reason"]
        if reason is not None and not isinstance(reason, str):
            raise ValueError("failure_reason must be a string or null")
        instance = cls(run_id=obj["run_id"], created_at=_parse_datetime(obj["created_at"], "created_at"),protocol_id=obj["protocol_id"], protocol_version=obj["protocol_version"],protocol_sha256=obj["protocol_sha256"],dataset=DatasetRevision.from_dict(obj["dataset"]),snapshots=tuple(CommitSnapshot.from_dict(x) for x in obj["snapshots"]),reviewer=ReviewerConfig.from_dict(obj["reviewer"]),tools=tuple(ToolVersion.from_dict(x) for x in obj["tools"]),budget=RunBudget.from_dict(obj["budget"]),environment=EnvironmentIdentity.from_dict(obj["environment"]),status=status,started_at=_parse_datetime(obj["started_at"], "started_at"),finished_at=_parse_datetime(obj["finished_at"], "finished_at"),artifacts=tuple(ArtifactReference.from_dict(x) for x in obj["artifacts"]),failure_reason=reason,schema_version=obj["schema_version"])  # type: ignore[arg-type]
        expected = obj["digest_sha256"]
        _sha(expected, "digest_sha256")
        if instance.digest_sha256 != expected:
            raise ValueError("manifest digest mismatch")
        return instance

    @classmethod
    def from_json(cls, text: str) -> BenchmarkRunManifest:
        if not isinstance(text, str):
            raise ValueError("manifest JSON must be text")
        try:
            data = json.loads(text, object_pairs_hook=_duplicate_rejecting_object,parse_constant=_reject_constant)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("manifest is not valid strict JSON") from exc
        return cls.from_dict(data)

    def transition(self, target: RunStatus, at: datetime, *,artifacts: tuple[ArtifactReference, ...] = (), failure_reason: str | None = None) -> BenchmarkRunManifest:
        """Return a new manifest for one permitted lifecycle transition."""
        _utc(at, "transition timestamp")
        allowed = {RunStatus.PLANNED: {RunStatus.RUNNING, RunStatus.CANCELLED},RunStatus.RUNNING: {RunStatus.COMPLETED, RunStatus.PARTIAL,RunStatus.FAILED, RunStatus.CANCELLED}}
        if not isinstance(target, RunStatus) or target not in allowed.get(self.status, set()):
            raise ValueError(f"invalid run-state transition: {self.status.value} -> {target!s}")
        if target == RunStatus.RUNNING:
            if at < self.created_at or artifacts or failure_reason is not None:
                raise ValueError("starting requires at >= created_at and no terminal data")
            return replace(self, status=target, started_at=at)
        if target == RunStatus.CANCELLED:
            if at < (self.started_at or self.created_at) or artifacts or failure_reason is not None:
                raise ValueError("cancellation timestamp/data is invalid")
            return replace(self, status=target, finished_at=at)
        if self.started_at is None or at < self.started_at:
            raise ValueError("terminal transition requires at >= started_at")
        return replace(self, status=target, finished_at=at,artifacts=artifacts, failure_reason=failure_reason)

    def write(self, path: str | os.PathLike[str]) -> None:
        """Atomically persist canonical JSON to a local application-owned path."""
        destination = Path(path)
        if not destination.parent.is_dir():
            raise ValueError("manifest destination parent directory must already exist")
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp",dir=destination.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(self.to_json())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    @classmethod
    def read(cls, path: str | os.PathLike[str]) -> BenchmarkRunManifest:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))
