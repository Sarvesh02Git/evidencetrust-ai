
import json

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
            status = "insufficient_evidence"

        return Claim(
            claim_id=claim_id,
            text=claim_text,
            status=status,
            explanation=str(data.get("explanation", "")),
            evidence_ids=valid_ids,
        )
