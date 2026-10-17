# EvidenceTrust AI — Starter Evaluation Dataset

This file contains 52 draft examples: four per each of the 13 PDFs supplied in `documents.zip`.

## Important research note
These are **draft labels for schema and pipeline testing**, not a final ground-truth benchmark and not evidence of model performance. Review each claim and passage against the full source PDF before using the file for research results. Some partial/contradicted examples are deliberately constructed adversarial cases and must be checked for whether the supplied passage truly warrants the label.

## Format
One JSON object per line (JSONL). Each row contains:
- `id`: unique example identifier
- `domain`: source topic
- `question`: evaluation question
- `claim`: one atomic or testable claim
- `expected_status`: `supported`, `contradicted`, `partially_supported`, or `insufficient_evidence`
- `expected_abstain`: expected answer-level abstention
- `evidence_passages`: evidence objects with `id`, `source`, `page`, and `text`
- `expected_evidence_ids`: evidence IDs expected to support/refute the claim

## Before research use
1. Check that the application's evaluation runner expects exactly these field names and types.
2. Verify source page numbers and passage wording in each PDF.
3. Have a human reviewer confirm each expected status and evidence ID.
4. Add separate examples for retrieval failure and citation mismatch if those are in scope.
5. Split training/tuning examples from the held-out evaluation set. Do not tune on the held-out set.
6. Report metrics only after a successful run on the reviewed labels.

The `insufficient_evidence` rows use an empty evidence list by design and should be reviewed to confirm how the runner handles absent evidence.
