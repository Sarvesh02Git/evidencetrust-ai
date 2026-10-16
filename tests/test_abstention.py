
import pytest

from app.abstention import determine_answer_status
from app.schemas import Claim


def make_claim(claim_id, status):
    return Claim(
        claim_id=claim_id,
        text=f"Test claim {claim_id}",
        status=status,
    )


def test_no_claims_means_abstention():
    status, abstained, reason = determine_answer_status([])

    assert status == "insufficient_evidence"
    assert abstained is True
    assert reason


def test_all_supported_claims():
    claims = [
        make_claim(1, "supported"),
        make_claim(2, "supported"),
    ]

    status, abstained, reason = determine_answer_status(claims)

    assert status == "supported"
    assert abstained is False
    assert reason is None


def test_all_insufficient_claims():
    claims = [
        make_claim(1, "insufficient_evidence"),
        make_claim(2, "insufficient_evidence"),
    ]

    status, abstained, reason = determine_answer_status(claims)

    assert status == "insufficient_evidence"
    assert abstained is True
    assert reason


def test_all_contradicted_claims():
    claims = [
        make_claim(1, "contradicted"),
        make_claim(2, "contradicted"),
    ]

    status, abstained, reason = determine_answer_status(claims)

    assert status == "contradicted"
    assert abstained is False
    assert reason


def test_mixed_supported_and_insufficient_claims():
    claims = [
        make_claim(1, "supported"),
        make_claim(2, "insufficient_evidence"),
    ]

    status, abstained, reason = determine_answer_status(claims)

    assert status == "partially_supported"
    assert abstained is False
    assert reason


def test_partially_supported_claim():
    claims = [make_claim(1, "partially_supported")]

    status, abstained, reason = determine_answer_status(claims)

    assert status == "partially_supported"
    assert abstained is False
    assert reason
