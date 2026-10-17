
from app.claim_extractor import ClaimExtractor


def test_abstention_message_is_not_extracted_as_a_claim():
    extractor = ClaimExtractor()

    assert extractor.extract(
        "There is insufficient evidence."
    ) == []


def test_generic_unverified_answer_is_not_extracted_as_a_claim():
    extractor = ClaimExtractor()

    answer = (
        "The answer could not be fully verified against "
        "the retrieved evidence. Review the claim-level results."
    )

    assert extractor.extract(answer) == []


def test_empty_answer_returns_no_claims():
    extractor = ClaimExtractor()

    assert extractor.extract("  ") == []

def test_abstention_with_specific_question_returns_no_claims():
    extractor = ClaimExtractor()

    assert extractor.extract(
        "Insufficient evidence to determine the capital of Japan."
    ) == []
