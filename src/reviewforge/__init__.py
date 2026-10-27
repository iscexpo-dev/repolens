"""Benchmark-first foundation for an AI code reviewer."""

from .versioning import (
    DEFAULT_COMPATIBILITY_POLICY,
    ComponentCompatibility,
    CompatibilityError,
    CompatibilityPolicy,
    migrate_legacy_record,
    validate_component_version,
)

__version__ = "0.1.0"

__all__ = [
    "CompatibilityError",
    "CompatibilityPolicy",
    "ComponentCompatibility",
    "DEFAULT_COMPATIBILITY_POLICY",
    "migrate_legacy_record",
    "validate_component_version",
]
