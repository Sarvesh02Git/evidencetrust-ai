
import pytest
import fitz

from app.document_loader import load_pdf_pages


def create_test_pdf(path):
    """Create a small PDF for isolated loader tests."""
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "EvidenceTrust loader test document.")
        pdf.save(path)


def test_load_pdf_pages_extracts_text_and_metadata(tmp_path):
    create_test_pdf(tmp_path / "sample.pdf")

    pages = load_pdf_pages(tmp_path)

    assert len(pages) == 1
    assert pages[0]["source"] == "sample.pdf"
    assert pages[0]["page"] == 1
    assert "EvidenceTrust loader test document." in pages[0]["text"]


def test_load_pdf_pages_rejects_missing_directory(tmp_path):
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        load_pdf_pages(missing_dir)


def test_load_pdf_pages_rejects_directory_without_pdfs(tmp_path):
    (tmp_path / "notes.txt").write_text(
        "This is not a PDF.", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="No PDF files found"):
        load_pdf_pages(tmp_path)


def test_load_pdf_pages_rejects_pdf_without_extractable_text(tmp_path):
    with fitz.open() as pdf:
        pdf.new_page()
        pdf.save(tmp_path / "blank.pdf")

    with pytest.raises(
        ValueError, match="No extractable PDF text found"
    ):
        load_pdf_pages(tmp_path)
