
from collections import Counter


def calculate_claim_metrics(
    predictions: list[str],
    references: list[str],
) -> dict:
    """Calculate classification metrics against reference labels."""

    if len(predictions) != len(references):
        raise ValueError(
            "Predictions and references must have equal lengths."
        )

    if not references:
        return {
            "sample_count": 0,
            "accuracy": None,
            "per_class": {},
        }

    allowed = {
        "supported",
        "contradicted",
        "partially_supported",
        "insufficient_evidence",
    }

    if any(label not in allowed for label in predictions + references):
        raise ValueError("An unknown classification label was supplied.")

    total = len(references)
    correct = sum(
        prediction == reference
        for prediction, reference in zip(predictions, references)
    )

    per_class = {}
    for label in sorted(allowed):
        tp = sum(
            prediction == label and reference == label
            for prediction, reference in zip(predictions, references)
        )
        fp = sum(
            prediction == label and reference != label
            for prediction, reference in zip(predictions, references)
        )
        fn = sum(
            prediction != label and reference == label
            for prediction, reference in zip(predictions, references)
        )

        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None
            and recall is not None
            and precision + recall > 0
            else 0.0 if precision is not None and recall is not None
            else None
        )

        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(reference == label for reference in references),
        }

    return {
        "sample_count": total,
        "accuracy": correct / total,
        "per_class": per_class,
    }


def calculate_claim_rates(
    total_claims: int,
    supported_claims: int,
    contradicted_claims: int,
    partially_supported_claims: int,
    insufficient_claims: int,
) -> dict:
    """Calculate descriptive claim-status proportions."""

    if total_claims < 0:
        raise ValueError("total_claims cannot be negative.")

    counts = [
        supported_claims,
        contradicted_claims,
        partially_supported_claims,
        insufficient_claims,
    ]

    if any(count < 0 for count in counts):
        raise ValueError("Claim counts cannot be negative.")

    if sum(counts) != total_claims:
        raise ValueError(
            "Claim-status counts must sum to total_claims."
        )

    if total_claims == 0:
        return {
            "total_claims": 0,
            "supported_rate": None,
            "contradicted_rate": None,
            "partially_supported_rate": None,
            "insufficient_evidence_rate": None,
        }

    return {
        "total_claims": total_claims,
        "supported_rate": supported_claims / total_claims,
        "contradicted_rate": contradicted_claims / total_claims,
        "partially_supported_rate": (
            partially_supported_claims / total_claims
        ),
        "insufficient_evidence_rate": insufficient_claims / total_claims,
    }

