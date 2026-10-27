import pytest

from reviewforge.benchmark.metrics import score_findings


def test_metrics_count_duplicates_as_false_positives():
    gold = [
        {"pr_id": "repo#1", "gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "gold_id": "G2", "severity": "low"},
    ]
    predictions = [
        {"pr_id": "repo#1", "prediction_id": "P1", "matched_gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "prediction_id": "P2", "matched_gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "prediction_id": "P3", "matched_gold_id": None, "severity": "low"},
    ]
    result = score_findings(gold, predictions)["overall"]
    assert result["true_positive"] == 1
    assert result["false_positive"] == 2
    assert result["false_negative"] == 1
    assert result["precision"] == pytest.approx(1 / 3)
    assert result["recall"] == pytest.approx(1 / 2)


def test_invalid_cross_pr_match_is_false_positive():
    gold = [{"pr_id": "repo#1", "gold_id": "G1"}]
    predictions = [{"pr_id": "repo#2", "prediction_id": "P1", "matched_gold_id": "G1"}]
    result = score_findings(gold, predictions)["overall"]
    assert result["false_positive"] == 1
    assert result["false_negative"] == 1


def test_duplicate_gold_ids_fail_fast():
    gold = [
        {"pr_id": "repo#1", "gold_id": "G1"},
        {"pr_id": "repo#1", "gold_id": "G1"},
    ]
    with pytest.raises(ValueError, match="duplicate gold_id"):
        score_findings(gold, [])


def test_empty_gold_and_predictions_use_zero_fallback_not_perfect_scores():
    result = score_findings([], [])

    assert result["overall"] == {
        "true_positive": 0,
        "false_positive": 0,
        "false_negative": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "f0_5": 0.0,
        "f2": 0.0,
    }
    assert result["gold_count"] == 0
    assert result["prediction_count"] == 0


def test_unmatched_prediction_and_empty_prediction_denominators():
    gold = [{"pr_id": "repo#1", "gold_id": "G1"}]
    unmatched_prediction = [
        {"pr_id": "repo#1", "prediction_id": "P1", "matched_gold_id": None}
    ]

    unmatched = score_findings(gold, unmatched_prediction)["overall"]
    assert (unmatched["true_positive"], unmatched["false_positive"]) == (0, 1)
    assert (unmatched["false_negative"], unmatched["precision"], unmatched["recall"]) == (
        1,
        0.0,
        0.0,
    )

    no_predictions = score_findings(gold, [])["overall"]
    assert no_predictions["false_negative"] == 1
    assert no_predictions["precision"] == 0.0
    assert no_predictions["recall"] == 0.0


def test_duplicate_prediction_is_penalized_in_its_gold_severity_slice():
    gold = [{"pr_id": "repo#1", "gold_id": "G1", "severity": "high"}]
    predictions = [
        {
            "pr_id": "repo#1",
            "prediction_id": "P1",
            "matched_gold_id": "G1",
            "severity": "high",
        },
        {
            "pr_id": "repo#1",
            "prediction_id": "P2",
            "matched_gold_id": "G1",
            "severity": "high",
        },
    ]

    result = score_findings(gold, predictions)
    assert result["overall"]["true_positive"] == 1
    assert result["overall"]["false_positive"] == 1
    assert result["by_gold_severity"]["high"]["true_positive"] == 1
    assert result["by_gold_severity"]["high"]["false_positive"] == 1
    assert result["by_gold_severity"]["high"]["precision"] == pytest.approx(0.5)


def test_ambiguous_adjudicated_matches_use_one_to_one_duplicate_penalty():
    gold = [
        {"pr_id": "repo#1", "gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "gold_id": "G2", "severity": "high"},
    ]
    predictions = [
        {"pr_id": "repo#1", "prediction_id": "P1", "matched_gold_id": "G1"},
        {"pr_id": "repo#1", "prediction_id": "P2", "matched_gold_id": "G1"},
        {"pr_id": "repo#1", "prediction_id": "P3", "matched_gold_id": "G2"},
    ]

    result = score_findings(gold, predictions)["overall"]

    assert result["true_positive"] == 2
    assert result["false_positive"] == 1
    assert result["false_negative"] == 0


def test_severity_disagreement_does_not_change_identity_match_but_is_sliced():
    gold = [
        {"pr_id": "repo#1", "gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "gold_id": "G2", "severity": "low"},
    ]
    predictions = [
        {
            "pr_id": "repo#1",
            "prediction_id": "P1",
            "matched_gold_id": "G1",
            "severity": "low",
        }
    ]

    result = score_findings(gold, predictions)
    assert result["overall"]["true_positive"] == 1
    assert result["by_gold_severity"]["high"]["recall"] == 1.0
    assert result["by_gold_severity"]["low"]["false_positive"] == 1


def test_category_disagreement_does_not_replace_adjudicated_identity():
    gold = [
        {
            "pr_id": "repo#1",
            "gold_id": "G1",
            "category": "correctness",
        }
    ]
    predictions = [
        {
            "pr_id": "repo#1",
            "prediction_id": "P1",
            "matched_gold_id": "G1",
            "category": "security",
        }
    ]

    result = score_findings(gold, predictions)
    assert result["overall"]["true_positive"] == 1
    assert "by_category" not in result


@pytest.mark.parametrize(
    ("gold", "predictions", "message"),
    [
        ([None], [], "each gold finding must be an object"),
        ([{"pr_id": 1, "gold_id": "G1"}], [], "non-empty pr_id and gold_id"),
        ([], [None], "each prediction must be an object"),
        (
            [],
            [{"pr_id": "repo#1", "matched_gold_id": 1}],
            "matched_gold_id must be a string or null",
        ),
    ],
)
def test_malformed_metric_records_fail_with_value_error(gold, predictions, message):
    with pytest.raises(ValueError, match=message):
        score_findings(gold, predictions)


def test_scoring_is_stable_for_repeated_identical_inputs():
    gold = [
        {"pr_id": "repo#1", "gold_id": "G1", "severity": "high"},
        {"pr_id": "repo#1", "gold_id": "G2", "severity": "low"},
    ]
    predictions = [
        {"pr_id": "repo#1", "prediction_id": "P1", "matched_gold_id": "G1"},
        {"pr_id": "repo#1", "prediction_id": "P2", "matched_gold_id": None},
    ]

    assert score_findings(gold, predictions) == score_findings(gold, predictions)
