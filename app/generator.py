
import json

from app.llm_client import GROQ_MODEL, get_groq_client
from app.schemas import EvidenceItem


class AnswerGenerator:
    def __init__(self):
        self.client = None

    def generate(
        self,
        question: str,
        evidence: list[EvidenceItem],
    ) -> dict:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if not evidence:
            return {
                "answer": "",
                "limitations": ["No evidence was provided."],
            }

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
Answer using only the supplied evidence.
Do not invent facts or use outside knowledge.
If evidence is insufficient, say so.
Cite evidence using IDs such as [E1].

Return JSON:
{"answer": "string", "limitations": ["string"]}
""",
                },
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{question}\n\n"
                        f"Evidence:\n{evidence_text}"
                    ),
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid JSON."
            ) from exc

        answer = result.get("answer")
        limitations = result.get("limitations", [])

        if not isinstance(answer, str):
            raise RuntimeError("Generated answer must be a string.")

        if not isinstance(limitations, list):
            limitations = []

        return {
            "answer": answer,
            "limitations": [
                str(item) for item in limitations
            ],
        }
