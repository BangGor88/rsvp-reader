import re
from typing import Any

import fitz

WORD_RE = re.compile(r"\S+")
MIN_TEXT_WORDS_FOR_NON_IMAGE = 20


def _page_words(page: fitz.Page) -> list[str]:
    raw_text = page.get_text("text") or ""
    text = re.sub(r"-\n", "", raw_text)
    return WORD_RE.findall(text)


def parse_pdf(pdf_path: str) -> dict[str, Any]:
    words: list[str] = []
    pages: list[dict[str, int]] = []

    doc = fitz.open(pdf_path)
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_words = _page_words(page)

            start = len(words)
            words.extend(page_words)
            end = len(words) - 1
            pages.append(
                {
                    "page": page_idx + 1,
                    "start_word": start,
                    "end_word": max(start, end),
                }
            )
    finally:
        doc.close()

    return {
        "words": words,
        "pages": pages,
        "word_count": len(words),
        "page_count": len(pages),
        "image_only": len(words) < MIN_TEXT_WORDS_FOR_NON_IMAGE and len(pages) > 0,
    }
