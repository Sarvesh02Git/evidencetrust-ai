
# EvidenceTrust AI

An evidence-grounded question-answering and verification prototype.

## Planned capabilities

- PDF extraction with page metadata
- Semantic retrieval using Sentence Transformers and FAISS
- Evidence-grounded answer generation
- Atomic factual claim extraction
- Claim-level support and contradiction judgments
- Insufficient-evidence handling and abstention
- Evaluation against human-annotated reference labels
- FastAPI interface

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies from requirements.txt.
3. Configure the model provider in a local .env file.
4. Place permitted PDF documents in data/documents/.
5. Start the API with:

   uvicorn app.api:app --reload

6. Open /docs on the local server to view the API interface.

## Research integrity

Similarity scores are not factual confidence scores.
Automated verification judgments require evaluation.
Report experimental results only after running documented experiments
against reference labels.
