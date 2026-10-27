"""Metrics for predictions matched to adjudicated gold findings.

This module deliberately does not perform semantic matching. Matching is a
separate, versioned operation that must be validated against human labels.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class Score:
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    f0_5: float
    f2: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _prf(tp: int, fp: int, fn: int) -> Score:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    def f_beta(beta: float) -> float:
        denom = beta * beta * precision + recall
        if denom == 0.0:
            return 0.0
        return (1 + beta * beta) * precision * recall / denom

    return Score(tp, fp, fn, precision, recall, f_beta(1.0), f_beta(0.5), f_beta(2.0))


def score_findings(
    gold_findings: Iterable[dict[str, Any]],
    predictions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Compute micro scores using `pr_id`, `gold_id`, and `matched_gold_id`.

    Input match decisions must be adjudicated/versioned outside this function.
    Prediction IDs are assumed to be unique within a PR; duplicate gold matches
    are counted as false positives to prevent double-credit.
    """
    gold_list = list(gold_findings)
    pred_list = list(predictions)

    gold_by_pr: dict[str, set[str]] = defaultdict(set)
    for item in gold_list:
        if not isinstance(item, dict):
            raise ValueError("each gold finding must be an object")
        pr_id = item.get("pr_id")
        gold_id = item.get("gold_id")
        if (
            not isinstance(pr_id, str)
            or not pr_id.strip()
            or not isinstance(gold_id, str)
            or not gold_id.strip()
        ):
            raise ValueError("each gold finding needs non-empty pr_id and gold_id")
        if gold_id in gold_by_pr[pr_id]:
            raise ValueError(f"duplicate gold_id {gold_id!r} for PR {pr_id!r}")
        gold_by_pr[pr_id].add(gold_id)

    matched_by_pr: dict[str, set[str]] = defaultdict(set)
    tp = fp = 0
    seen_prediction_ids: set[tuple[str, str]] = set()
    duplicate_prediction_indexes: set[int] = set()

    for index, item in enumerate(pred_list):
        if not isinstance(item, dict):
            raise ValueError("each prediction must be an object")
        pr_id = item.get("pr_id")
        if not isinstance(pr_id, str) or not pr_id.strip():
            raise ValueError("each prediction needs a non-empty pr_id")
        raw_prediction_id = item.get("prediction_id", f"row-{index}")
        if not isinstance(raw_prediction_id, str) or not raw_prediction_id.strip():
            raise ValueError("each prediction needs a non-empty prediction_id")
        identity = (pr_id, raw_prediction_id)
        if identity in seen_prediction_ids:
            raise ValueError(
                f"duplicate prediction_id {raw_prediction_id!r} for PR {pr_id!r}"
            )
        seen_prediction_ids.add(identity)

        raw_match = item.get("matched_gold_id")
        if raw_match is None:
            fp += 1
            continue
        if not isinstance(raw_match, str):
            raise ValueError("matched_gold_id must be a string or null")
        if not raw_match.strip():
            fp += 1
            continue

        gold_id = raw_match
        if gold_id not in gold_by_pr.get(pr_id, set()):
            # Invalid cross-PR or nonexistent matches cannot earn credit.
            fp += 1
            continue
        if gold_id in matched_by_pr[pr_id]:
            # Duplicate comments about one issue are still review noise.
            fp += 1
            duplicate_prediction_indexes.add(index)
            continue

        matched_by_pr[pr_id].add(gold_id)
        tp += 1

    total_gold = sum(len(items) for items in gold_by_pr.values())
    fn = total_gold - tp
    overall = _prf(tp, fp, fn)

    by_severity: dict[str, dict[str, Any]] = {}
    for severity in sorted({str(g.get("severity", "unknown")).lower() for g in gold_list}):
        target = {
            (str(g["pr_id"]), str(g["gold_id"]))
            for g in gold_list
            if str(g.get("severity", "unknown")).lower() == severity
        }
        severity_tp = sum(
            1 for pr_id, gold_id in target if gold_id in matched_by_pr.get(pr_id, set())
        )
        severity_fn = len(target) - severity_tp
        # The severity-specific precision denominator includes predictions that
        # the adjudicator matched to this severity's gold issues, plus unmatched
        # predictions carrying this severity. This is a diagnostic slice only.
        severity_fp = 0
        for index, item in enumerate(pred_list):
            pred_sev = str(item.get("severity", "unknown")).lower()
            if pred_sev != severity:
                continue
            if index in duplicate_prediction_indexes:
                severity_fp += 1
                continue
            raw_match = item.get("matched_gold_id")
            if raw_match is None or raw_match == "":
                severity_fp += 1
                continue
            if (str(item.get("pr_id", "")), str(raw_match)) not in target:
                severity_fp += 1
        by_severity[severity] = _prf(severity_tp, severity_fp, severity_fn).to_dict()

    return {
        "overall": overall.to_dict(),
        "gold_count": total_gold,
        "prediction_count": len(pred_list),
        "by_gold_severity": by_severity,
        "matching_policy": "adjudicated matched_gold_id; duplicate matches count as false positives",
        "caveat": "No semantic matching or confidence intervals are performed by this scorer.",
    }
