
import json
import re

from app.llm_client import GROQ_MODEL, get_groq_client
from app.schemas import Claim, EvidenceItem


class ClaimVerifier:
    ALLOWED_STATUSES = {
        "supported",
        "contradicted",
        "partially_supported",
        "insufficient_evidence",
    }

    def __init__(self):
        self.client = None

    @staticmethod
    def _fallback_evidence_ids(claim_text: str, evidence: list[EvidenceItem]) -> list[int]:
        """Find plausible citation passages when the LLM omits citations.

        This is a citation-repair heuristic only: it never upgrades an
        insufficient/partial status to supported. It preserves the rule that
        supported/contradicted claims require a citation.
        """
        stopwords = {
            "the", "a", "an", "and", "or", "to", "of", "for", "in",
            "on", "by", "with", "that", "this", "must", "shall", "should",
            "is", "are", "be", "as", "its", "their", "it", "from", "into",
            "ensure", "ensures", "ensuring", "organization", "information",
        }

        def terms(text: str) -> set[str]:
            words = re.findall(r"[a-z0-9]+", text.lower())
            result = set()
            for word in words:
                if word in stopwords or len(word) < 3:
                    continue
                # Small morphology normalization for common inflections.
                if word.endswith("ing") and len(word) > 5:
                    word = word[:-3]
                elif word.endswith("ed") and len(word) > 4:
                    word = word[:-2]
                elif word.endswith("s") and len(word) > 4:
                    word = word[:-1]
                result.add(word)
            return result

        claim_terms = terms(claim_text)
        if not claim_terms:
            return []

        scored = []
        for index, item in enumerate(evidence, start=1):
            evidence_terms = terms(item.text)
            overlap = len(claim_terms & evidence_terms)
            coverage = overlap / len(claim_terms)
            # Conservative threshold: require at least two meaningful terms
            # and 40% claim-term coverage before repairing a citation.
            if overlap >= min(2, len(claim_terms)) and coverage >= 0.4:
                scored.append((coverage, overlap, index))

        scored.sort(reverse=True)
        return [item[2] for item in scored[:2]]

    def verify(
        self,
        claim_text: str,
        evidence: list[EvidenceItem],
        claim_id: int,
    ) -> Claim:
        if not evidence:
            return Claim(
                claim_id=claim_id,
                text=claim_text,
                status="insufficient_evidence",
                explanation="No evidence was available.",
            )

        if self.client is None:
            self.client = get_groq_client()

        evidence_text = "\n\n".join(
            f"[E{i}] Source: {item.source}, page: {item.page}\n"
            f"{item.text}"
            for i, item in enumerate(evidence, start=1)
        )

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """
Judge the claim using only the supplied evidence.

Statuses:
- supported: the evidence supports the full claim.
- contradicted: the evidence directly conflicts with the claim.
- partially_supported: only some material parts are supported.
- insufficient_evidence: the evidence cannot determine the claim.

Missing evidence is not proof of contradiction.
Use only the supplied evidence IDs.
For supported or contradicted, cite at least one relevant evidence ID.

Return JSON:
{
  "status": "supported",
  "explanation": "brief reasoning",
  "evidence_ids": [1]
}
""",
                },
                {
                    "role": "user",
                    "content": (
                        f"Claim:\n{claim_text}\n\n"
                        f"Evidence:\n{evidence_text}"
                    ),
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid verification JSON."
            ) from exc

        status = data.get("status")

        if status not in self.ALLOWED_STATUSES:
            raise RuntimeError(
                f"Unexpected verification status: {status}"
            )

        raw_ids = data.get("evidence_ids", [])
        if not isinstance(raw_ids, list):
            raw_ids = []

        valid_ids = sorted({
            item for item in raw_ids
            if type(item) is int and 1 <= item <= len(evidence)
        })

        if status in {"supported", "contradicted"} and not valid_ids:
            # Repair missing/invalid citations only when the supplied passage
            # has meaningful lexical overlap with the claim. Never invent IDs.
            valid_ids = self._fallback_evidence_ids(claim_text, evidence)
            if not valid_ids:
                status = "insufficient_evidence"

        return Claim(
            claim_id=claim_id,
            text=claim_text,
            status=status,
            explanation=str(data.get("explanation", "")),
            evidence_ids=valid_ids,
        )
