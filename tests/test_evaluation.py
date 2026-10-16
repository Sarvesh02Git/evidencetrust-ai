
import unittest

from app.evaluation import (
    calculate_claim_metrics,
    calculate_claim_rates,
)


def test_perfect_classification():
    labels = ["supported", "contradicted"]

    result = calculate_claim_metrics(labels, labels)

    assert result["sample_count"] == 2
    assert result["accuracy"] == 1.0


def test_empty_evaluation():
    result = calculate_claim_metrics([], [])

    assert result["sample_count"] == 0
    assert result["accuracy"] is None


def test_mismatched_lengths():
    with unittest.TestCase().assertRaises(ValueError):
        calculate_claim_metrics(["supported"], [])


def test_claim_rates():
    result = calculate_claim_rates(
        total_claims=4,
        supported_claims=2,
        contradicted_claims=1,
        partially_supported_claims=0,
        insufficient_claims=1,
    )

    assert result["supported_rate"] == 0.5
    assert result["contradicted_rate"] == 0.25
    assert result["insufficient_evidence_rate"] == 0.25


def test_claim_rates_reject_inconsistent_counts():
    with unittest.TestCase().assertRaises(ValueError):
        calculate_claim_rates(
            total_claims=5,
            supported_claims=2,
            contradicted_claims=1,
            partially_supported_claims=0,
            insufficient_claims=1,
        )
