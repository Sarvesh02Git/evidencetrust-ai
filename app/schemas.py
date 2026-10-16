
from typing import Literal

from pydantic import BaseModel, Field


ClaimStatus = Literal[
    "supported",
    "contradicted",
    "insufficient_evidence",
    "partially_supported",
]

AnswerStatus = Literal[
    "supported",
    "contradicted",
    "partially_supported",
    "insufficient_evidence",
]


class EvidenceItem(BaseModel):
    source: str
    page: int = Field(ge=1)
    chunk_id: int
    text: str
    similarity: float | None = None


class Claim(BaseModel):
    claim_id: int = Field(ge=1)
    text: str
    status: ClaimStatus = "insufficient_evidence"
    explanation: str = ""
    evidence_ids: list[int] = Field(default_factory=list)


class VerificationResult(BaseModel):
    question: str
    answer: str
    status: AnswerStatus
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    abstained: bool = False
    abstention_reason: str | None = None
    limitations: list[str] = Field(default_factory=list)
