
import json
from unittest.mock import MagicMock

import pytest

from app.verifier import ClaimVerifier
from app.schemas import EvidenceItem


@pytest.fixture
def evidence():
    return [
        EvidenceItem(
            source="security.pdf",
            page=5,
            chunk_id=10,
            text="Top management shall demonstrate leadership and commitment.",
            similarity=0.9,
        ),
        EvidenceItem(
            source="security.pdf",
            page=8,
            chunk_id=15,
            text="The organization shall define its risk assessment process.",
            similarity=0.8,
        ),
    ]


def make_verifier(response_data):
    verifier = ClaimVerifier()
    verifier.client = MagicMock()

    response = MagicMock()
    response.choices[0].message.content = json.dumps(response_data)
    verifier.client.chat.completions.create.return_value = response

    return verifier


def test_verify_supported_claim(evidence):
    verifier = make_verifier({
        "status": "supported",
        "explanation": "The first passage directly supports the claim.",
        "evidence_ids": [1],
    })

    result = verifier.verify(
        "Top management must demonstrate leadership.",
        evidence,
        claim_id=1,
    )

    assert result.status == "supported"
    assert result.claim_id == 1
    assert result.evidence_ids == [1]


def test_verify_insufficient_evidence(evidence):
    verifier = make_verifier({
        "status": "insufficient_evidence",
        "explanation": "The passages do not establish this claim.",
        "evidence_ids": [],
    })

    result = verifier.verify(
        "The organization has 500 employees.",
        evidence,
        claim_id=2,
    )

    assert result.status == "insufficient_evidence"
    assert result.evidence_ids == []



def test_verify_repairs_invalid_evidence_id_when_matching_passage_exists(evidence):
    verifier = make_verifier({
        "status": "supported",
        "explanation": "Claim supported.",
        "evidence_ids": [99],
    })

    result = verifier.verify(
        "Top management must demonstrate leadership.",
        evidence,
        claim_id=1,
    )

    # The invalid ID is discarded; a matching supplied passage is selected.
    assert result.status == "supported"
    assert result.evidence_ids == [1]




def test_repairs_missing_citation_when_evidence_contains_claim(evidence):
    verifier = make_verifier({
        "status": "supported",
        "explanation": "The evidence supports the claim.",
        "evidence_ids": [],
    })

    result = verifier.verify(
        "Top management must demonstrate leadership and commitment.",
        evidence,
        claim_id=3,
    )

    assert result.status == "supported"
    assert result.evidence_ids == [1]


def test_missing_citation_without_matching_evidence_is_downgraded(evidence):
    verifier = make_verifier({
        "status": "supported",
        "explanation": "No matching passage was cited.",
        "evidence_ids": [],
    })

    result = verifier.verify(
        "The chief executive has a private mobile telephone number.",
        evidence,
        claim_id=4,
    )

    assert result.status == "insufficient_evidence"
    assert result.evidence_ids == []
