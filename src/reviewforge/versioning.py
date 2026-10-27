"""Versioning and compatibility policy for review-system contracts.

The project keeps versioned interfaces separate by component. A versioned record
may evolve independently, but any migration must be explicit and traceable. This
module defines the compatibility policy used for API schemas, finding records,
prompt/config metadata, and benchmark manifests without storing secrets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Final, Mapping

_SEMVER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


class CompatibilityError(ValueError):
    """Raised when a version is unsupported or cannot be migrated safely."""


def _require_semver(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _SEMVER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a semantic version, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class ComponentCompatibility:
    component: str
    current_version: str
    supported_versions: tuple[str, ...]
    legacy_migrations: Mapping[str, str] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        _require_semver(self.current_version, "current_version")
        for version in self.supported_versions:
            _require_semver(version, "supported_versions")
        if self.current_version not in self.supported_versions:
            raise ValueError(
                f"component {self.component!r} must include the current version in supported_versions"
            )
        for legacy, target in self.legacy_migrations.items():
            _require_semver(legacy, f"legacy_migrations[{legacy!r}]")
            _require_semver(target, f"legacy_migrations[{legacy!r}]")
            if target not in self.supported_versions:
                raise ValueError(
                    f"legacy migration target {target!r} for {self.component!r} must be supported"
                )

    def validate(self, version: str) -> str:
        """Return the accepted version or raise CompatibilityError."""
        candidate = _require_semver(version, "version")
        if candidate in self.supported_versions or candidate == self.current_version:
            return candidate
        if candidate in self.legacy_migrations:
            return candidate
        raise CompatibilityError(
            f"unsupported {self.component} version {candidate!r}; supported versions are "
            f"{', '.join(self.supported_versions)}"
        )

    def migrate(self, payload: Mapping[str, Any], version: str | None = None) -> dict[str, Any]:
        """Migrate a legacy payload to the current supported representation.

        A migration is explicit and traceable instead of silently rewriting history.
        """
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")

        raw_version = version or str(payload.get("schema_version") or payload.get("version") or self.current_version)
        accepted = self.validate(raw_version)
        migrated = dict(payload)

        if accepted in self.legacy_migrations:
            target = self.legacy_migrations[accepted]
            migrated["schema_version"] = target
            migrated["compatibility_migration"] = {
                "component": self.component,
                "from": accepted,
                "to": target,
                "reason": "explicit legacy migration",
            }
            if "version" in migrated and isinstance(migrated["version"], str):
                migrated["version"] = target
            return migrated

        migrated["schema_version"] = self.current_version
        if "version" in migrated and isinstance(migrated["version"], str):
            migrated["version"] = self.current_version
        return migrated


@dataclass(frozen=True, slots=True)
class CompatibilityPolicy:
    components: tuple[ComponentCompatibility, ...]

    def __post_init__(self) -> None:
        if not self.components:
            raise ValueError("components must not be empty")

    def for_component(self, name: str) -> ComponentCompatibility:
        for component in self.components:
            if component.component == name:
                return component
        raise KeyError(f"unknown component: {name!r}")

    def validate(self, component: str, version: str) -> str:
        return self.for_component(component).validate(version)

    def migrate(self, component: str, payload: Mapping[str, Any], version: str | None = None) -> dict[str, Any]:
        return self.for_component(component).migrate(payload, version=version)


DEFAULT_COMPATIBILITY_POLICY = CompatibilityPolicy(
    components=(
        ComponentCompatibility(
            component="api",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="HTTP and internal API contracts, request/response schemas, and compatibility negotiation.",
        ),
        ComponentCompatibility(
            component="finding",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Normalized finding schema and evidence references.",
        ),
        ComponentCompatibility(
            component="prompt",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Prompt template and system-message versions.",
        ),
        ComponentCompatibility(
            component="context_policy",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Repository-context retrieval policy and ranking configuration.",
        ),
        ComponentCompatibility(
            component="model_config",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Model/provider configuration and budget metadata.",
        ),
        ComponentCompatibility(
            component="dataset",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Dataset revision and inclusion policy versions.",
        ),
        ComponentCompatibility(
            component="benchmark_manifest",
            current_version="1.0.0",
            supported_versions=("1.0.0",),
            legacy_migrations={"0.9.0": "1.0.0"},
            description="Benchmark run metadata and artifact provenance manifest.",
        ),
    )
)


def validate_component_version(component: str, version: str) -> str:
    return DEFAULT_COMPATIBILITY_POLICY.validate(component, version)


def migrate_legacy_record(component: str, payload: Mapping[str, Any], version: str | None = None) -> dict[str, Any]:
    return DEFAULT_COMPATIBILITY_POLICY.migrate(component, payload, version=version)
