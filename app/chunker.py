
import re

from app.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE


def split_into_units(text: str) -> list[str]:
    """Split text into paragraph- or sentence-sized units."""

    paragraphs = re.split(r"\n\s*\n+", text.strip())
    units = []

    for paragraph in paragraphs:
        paragraph = re.sub(r"\s+", " ", paragraph).strip()

        if not paragraph:
            continue

        # Keep short paragraphs and clause headings intact.
        if len(paragraph.split()) <= 80:
            units.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)

        for sentence in sentences:
            sentence = sentence.strip()

            if sentence:
                units.append(sentence)

    return units


def chunk_pages(
    pages: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """Create word-limited chunks with source and page metadata."""

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "chunk_size must be positive and "
            "0 <= overlap < chunk_size"
        )

    chunks = []
    step = chunk_size - overlap

    for page_data in pages:
        units = split_into_units(page_data["text"])
        current_words = []

        for unit in units:
            unit_words = unit.split()

            # Handle unusually long individual units.
            if len(unit_words) > chunk_size:
                if current_words:
                    chunks.append({
                        **page_data,
                        "text": " ".join(current_words),
                    })
                    current_words = []

                for start in range(0, len(unit_words), step):
                    part = unit_words[start:start + chunk_size]

                    if part:
                        chunks.append({
                            **page_data,
                            "text": " ".join(part),
                        })

                continue

            if (
                current_words
                and len(current_words) + len(unit_words) > chunk_size
            ):
                chunks.append({
                    **page_data,
                    "text": " ".join(current_words),
                })

                current_words = current_words[-overlap:] if overlap else []

            current_words.extend(unit_words)

        if current_words:
            chunks.append({
                **page_data,
                "text": " ".join(current_words),
            })

    for chunk_id, chunk in enumerate(chunks):
        chunk["chunk_id"] = chunk_id

    return chunks
