
from pathlib import Path

import fitz


def load_pdf_pages(documents_dir: Path) -> list[dict]:
    """Extract text from PDFs while preserving source and page metadata."""

    if not documents_dir.exists():
        raise FileNotFoundError(
            f"Documents directory not found: {documents_dir}"
        )

    pdf_files = sorted(documents_dir.glob("*.pdf"))

    if not pdf_files:
        raise ValueError(
            f"No PDF files found in {documents_dir}"
        )

    pages = []

    for pdf_path in pdf_files:
        try:
            with fitz.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf, start=1):
                    text = page.get_text("text").strip()

                    if not text:
                        continue

                    pages.append({
                        "source": pdf_path.name,
                        "page": page_number,
                        "text": text,
                    })

        except Exception as exc:
            raise RuntimeError(
                f"Could not process {pdf_path.name}: {exc}"
            ) from exc

    if not pages:
        raise ValueError(
            "No extractable PDF text found. "
            "The documents may be scanned or image-only."
        )

    return pages
