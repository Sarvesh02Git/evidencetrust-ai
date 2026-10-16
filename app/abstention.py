
from app.schemas import Claim, AnswerStatus


def determine_answer_status(
    claims: list[Claim],
) -> tuple[AnswerStatus, bool, str | None]:
    """Aggregate claim judgments into an answer-level decision."""

    if not claims:
        return (
            "insufficient_evidence",
            True,
            "No verifiable factual claims were available.",
        )

    statuses = [claim.status for claim in claims]

    supported = statuses.count("supported")
    contradicted = statuses.count("contradicted")
    partial = statuses.count("partially_supported")
    insufficient = statuses.count("insufficient_evidence")

    if contradicted == len(claims):
        return (
            "contradicted",
            False,
            "All assessed claims were contradicted by the evidence.",
        )

    if insufficient == len(claims):
        return (
            "insufficient_evidence",
            True,
            "The available evidence was insufficient to verify the claims.",
        )

    if partial or (supported and (contradicted or insufficient)):
        return (
            "partially_supported",
            False,
            "The answer contains a mixture of supported, "
            "contradicted, or unresolved claims.",
        )

    if contradicted:
        return (
            "partially_supported",
            False,
            "At least one claim is contradicted; review the individual claims.",
        )

    if insufficient:
        return (
            "partially_supported",
            False,
            "Some claims remain unverified, so the answer needs qualification.",
        )

    return ("supported", False, None)
