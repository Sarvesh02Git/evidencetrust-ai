
from app.chunker import chunk_pages
from app.config import DOCUMENTS_DIR
from app.document_loader import load_pdf_pages
from app.logging_config import configure_logging, logger
from app.pipeline import EvidenceTrustPipeline
from app.retriever import EvidenceRetriever


def build_pipeline() -> EvidenceTrustPipeline:
    pages = load_pdf_pages(DOCUMENTS_DIR)
    chunks = chunk_pages(pages)

    logger.info(
        "Loaded %d pages and created %d chunks.",
        len(pages),
        len(chunks),
    )

    retriever = EvidenceRetriever()
    retriever.build_index(chunks)

    return EvidenceTrustPipeline(retriever)


def main():
    configure_logging()
    print("\n=== EvidenceTrust AI ===\n")

    pipeline = build_pipeline()

    print("Pipeline initialized.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Your question: ").strip()

        if question.lower() in {"exit", "quit"}:
            break

        if not question:
            print("Enter a question.\n")
            continue

        try:
            result = pipeline.answer(question)

            print("\n--- Answer ---")
            print(result.answer or "(No answer provided)")
            print(f"\nStatus: {result.status}")
            print(f"Abstained: {result.abstained}")

            if result.abstention_reason:
                print(f"Reason: {result.abstention_reason}")

            print("\n--- Claims ---")
            for claim in result.claims:
                print(f"\n[{claim.claim_id}] {claim.text}")
                print(f"Status: {claim.status}")
                print(f"Explanation: {claim.explanation}")
                print(f"Evidence IDs: {claim.evidence_ids}")

            print("\n--- Evidence ---")
            for index, item in enumerate(result.evidence, start=1):
                print(
                    f"\n[E{index}] {item.source}, page {item.page}, "
                    f"similarity={item.similarity}"
                )
                print(item.text)

            print()

        except Exception:
            logger.exception("CLI request failed.")
            print(
                "The request could not be completed. "
                "Check logs/evidencetrust.log.\n"
            )


if __name__ == "__main__":
    main()
