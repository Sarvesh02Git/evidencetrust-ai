
import logging

from app.abstention import determine_answer_status
from app.claim_extractor import ClaimExtractor
from app.generator import AnswerGenerator
from app.retriever import EvidenceRetriever
from app.schemas import EvidenceItem, VerificationResult
from app.verifier import ClaimVerifier

logger = logging.getLogger("evidencetrust.pipeline")


class EvidenceTrustPipeline:
    def __init__(self, retriever: EvidenceRetriever):
        self.retriever = retriever
        self.generator = AnswerGenerator()
        self.claim_extractor = ClaimExtractor()
        self.verifier = ClaimVerifier()

    def answer(self, question: str, top_k: int = 5) -> VerificationResult:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        retrieved = self.retriever.search(
            question=question,
            top_k=top_k,
        )

        evidence = [
            EvidenceItem(
                source=item["source"],
                page=item["page"],
                chunk_id=item["chunk_id"],
                text=item["text"],
                similarity=item["similarity"],
            )
            for item in retrieved
        ]

        if not evidence:
            logger.info("No evidence retrieved for a question.")
            return VerificationResult(
                question=question,
                answer="",
                status="insufficient_evidence",
                abstained=True,
                abstention_reason="No evidence passages were retrieved.",
                limitations=["No evidence was available for verification."],
            )

        draft = self.generator.generate(question, evidence)
        draft_answer = draft["answer"]

        if not draft_answer.strip():
            return VerificationResult(
                question=question,
                answer="",
                status="insufficient_evidence",
                evidence=evidence,
                abstained=True,
                abstention_reason="The generator returned no answer.",
                limitations=draft["limitations"],
            )

        claim_texts = self.claim_extractor.extract(draft_answer)

        if not claim_texts:
            return VerificationResult(
                question=question,
                answer="",
                status="insufficient_evidence",
                evidence=evidence,
                abstained=True,
                abstention_reason="No verifiable factual claims were extracted.",
                limitations=draft["limitations"],
            )

        claims = [
            self.verifier.verify(
                claim_text=text,
                evidence=evidence,
                claim_id=index,
            )
            for index, text in enumerate(claim_texts, start=1)
        ]

        status, abstained, reason = determine_answer_status(claims)

        # Avoid presenting a mixed or contradicted answer as fully verified.
        if status != "supported":
            final_answer = (
                "The answer could not be fully verified against the "
                "retrieved evidence. Review the claim-level results."
            )
        else:
            final_answer = draft_answer

        limitations = list(draft["limitations"])
        if status != "supported":
            limitations.append(
                "The answer-level result is not fully supported. "
                "Inspect each claim and its cited evidence."
            )

        logger.info(
            "Completed pipeline request: status=%s, claims=%d, abstained=%s",
            status,
            len(claims),
            abstained,
        )

        return VerificationResult(
            question=question,
            answer=final_answer,
            status=status,
            claims=claims,
            evidence=evidence,
            abstained=abstained,
            abstention_reason=reason,
            limitations=limitations,
        )
