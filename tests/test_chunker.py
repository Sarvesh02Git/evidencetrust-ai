
import pytest

from app.chunker import chunk_pages, split_into_units


def test_split_into_units_preserves_text():
    text = "First paragraph.\n\nSecond paragraph."
    units = split_into_units(text)

    assert len(units) == 2
    assert units[0] == "First paragraph."
    assert units[1] == "Second paragraph."


def test_split_into_units_empty_text():
    assert split_into_units("") == []
    assert split_into_units("   ") == []


def test_chunk_pages_preserves_source_and_page():
    pages = [
        {
            "source": "sample.pdf",
            "page": 3,
            "text": "This is a sample paragraph for testing.",
        }
    ]

    chunks = chunk_pages(pages, chunk_size=10, overlap=2)

    assert len(chunks) >= 1
    assert chunks[0]["source"] == "sample.pdf"
    assert chunks[0]["page"] == 3
    assert chunks[0]["chunk_id"] == 0
    assert chunks[0]["text"]


def test_chunk_pages_assigns_unique_chunk_ids():
    pages = [
        {
            "source": "sample.pdf",
            "page": 1,
            "text": " ".join(
                f"word{i}" for i in range(30)
            ),
        }
    ]

    chunks = chunk_pages(pages, chunk_size=10, overlap=2)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    assert len(chunks) > 1
    assert chunk_ids == list(range(len(chunks)))


@pytest.mark.parametrize(
    "chunk_size, overlap",
    [
        (0, 0),
        (-1, 0),
        (10, -1),
        (10, 10),
        (5, 6),
    ],
)
def test_chunk_pages_rejects_invalid_parameters(
    chunk_size, overlap
):
    with pytest.raises(ValueError):
        chunk_pages(
            [{"source": "sample.pdf", "page": 1, "text": "Some text."}],
            chunk_size=chunk_size,
            overlap=overlap,
        )
