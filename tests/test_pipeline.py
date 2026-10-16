
from unittest.mock import MagicMock

import pytest

from app.pipeline import EvidenceTrustPipeline


@pytest.fixture
def pipeline():
    retriever = MagicMock()
    instance = EvidenceTrustPipeline(retriever)

    # Replace AI components with predictable mocks.
    instance.generator = MagicMock()
    instance.claim_extractor = MagicMock()
    instance.verifier = MagicMock()

    retriever.search.return_value = [
        {
            "source": "security.pdf",
            "page": 1,
            "chunk_id": 0,
            "text": "Top management shall demonstrate leadership.",
            "similarity": 0.9,
        }
    ]

    instance.generator.generate.return_value = {
        "answer": "Top management must demonstrate leadership.",
        "limitations": [],
    }

    instance.claim_extractor.extract.return_value = [
        "Top management must demonstrate leadership."
    ]

    return instance


def test_pipeline_rejects_empty_question(pipeline):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        pipeline.answer("   ")


def test_pipeline_abstains_when_no_evidence(pipeline):
    pipeline.retriever.search.return_value = []

    result = pipeline.answer("What must top management do?")

    assert result.status == "insufficient_evidence"
    assert result.abstained is True
    assert result.evidence == []
    pipeline.generator.generate.assert_not_called()


def test_pipeline_abstains_when_generator_returns_empty_answer(pipeline):
    pipeline.generator.generate.return_value = {
        "answer": "",
        "limitations": ["No answer generated."],
    }

    result = pipeline.answer("What must top management do?")

    assert result.status == "insufficient_evidence"
    assert result.abstained is True
    assert result.answer == ""


def test_pipeline_abstains_when_no_claims_are_extracted(pipeline):
    pipeline.claim_extractor.extract.return_value = []

    result = pipeline.answer("What must top management do?")

    assert result.status == "insufficient_evidence"
    assert result.abstained is True
    assert result.claims == []


def test_pipeline_returns_fully_supported_answer(pipeline):
    from app.schemas import Claim

    pipeline.verifier.verify.return_value = Claim(
        claim_id=1,
        text="Top management must demonstrate leadership.",
        status="supported",
        explanation="The evidence supports this claim.",
        evidence_ids=[1],
    )

    result = pipeline.answer("What must top management do?")

    assert result.status == "supported"
    assert result.abstained is False
    assert result.answer == (
        "Top management must demonstrate leadership."
    )
    assert len(result.claims) == 1
    assert len(result.evidence) == 1


def test_pipeline_does_not_present_unverified_answer_as_verified(pipeline):
    from app.schemas import Claim

    pipeline.verifier.verify.return_value = Claim(
        claim_id=1,
        text="The organization has 500 employees.",
        status="insufficient_evidence",
        explanation="The evidence does not establish this.",
        evidence_ids=[],
    )

    result = pipeline.answer("How many employees are there?")

    assert result.status == "insufficient_evidence"
    assert result.answer != (
        "The organization has 500 employees."
    )
    assert result.limitations
