
import json
import re

from app.llm_client import GROQ_MODEL, get_groq_client


class ClaimExtractor:
    def __init__(self):
        self.client = None

    def extract(self, answer: str) -> list[str]:
        if not answer or not answer.strip():
            return []

        normalized = re.sub(r"\s+", " ", answer).strip().lower()

        # These are uncertainty messages, not factual claims.
        
        abstention_patterns = (
            r"^there is insufficient evidence\b.*$",
            r"^insufficient evidence\b.*$",
            r"^the answer could not be fully verified\b.*$",
            r"^i (?:cannot|can't) answer\b.*$",
            r"^the available evidence (?:is|was) insufficient\b.*$",
            r"^i do not have enough evidence\b.*$",
            r"^there is not enough evidence\b.*$",
            r"^unable to determine\b.*$",
            r"^cannot determine\b.*$",
            r"^i cannot determine\b.*$",
            r"^the evidence does not establish\b.*$",
        )


        if any(
            re.match(pattern, normalized)
            for pattern in abstention_patterns
        ):
            return []

        if self.client is None:
            self.client = get_groq_client()

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """
Extract atomic, verifiable factual claims from the answer.
Preserve names, numbers, dates, and qualifications.
Do not introduce new facts.
Ignore conversational filler.

If the answer only expresses uncertainty, abstention,
or inability to verify, return an empty claims list.

Return valid JSON:
{"claims": ["claim one", "claim two"]}
""",
                },
                {
                    "role": "user",
                    "content": answer,
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
                "Groq returned invalid claim JSON."
            ) from exc

        claims = data.get("claims", [])

        if not isinstance(claims, list):
            raise RuntimeError("'claims' must be a list.")

        return [
            claim.strip()
            for claim in claims
            if isinstance(claim, str) and claim.strip()
        ]
