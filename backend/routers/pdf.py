import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.pdf_service import parse_pdf

router = APIRouter(prefix="/pdf", tags=["pdf"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path.cwd() / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ParsedDocument = dict[str, Any]
pdf_cache: dict[str, ParsedDocument] = {}


def _doc_path(doc_id: str) -> Path:
    return UPLOAD_DIR / f"{doc_id}.pdf"


def _public_doc_payload(doc_id: str, parsed: ParsedDocument) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "word_count": parsed["word_count"],
        "page_count": parsed["page_count"],
        "pages": parsed["pages"],
        "image_only": parsed["image_only"],
    }


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are supported.")

    doc_id = str(uuid.uuid4())
    target_path = _doc_path(doc_id)

    content = await file.read()
    target_path.write_bytes(content)

    try:
        parsed = parse_pdf(str(target_path))
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Unable to parse PDF: {exc}") from exc

    pdf_cache[doc_id] = parsed
    return _public_doc_payload(doc_id, parsed)


@router.get("/words/{doc_id}")
def get_words(doc_id: str):
    cached = pdf_cache.get(doc_id)
    if cached:
        return {"words": cached["words"], "pages": cached["pages"]}

    file_path = _doc_path(doc_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")

    parsed = parse_pdf(str(file_path))
    pdf_cache[doc_id] = parsed
    return {"words": parsed["words"], "pages": parsed["pages"]}


@router.delete("/{doc_id}")
def clear_doc(doc_id: str):
    pdf_cache.pop(doc_id, None)
    target = _doc_path(doc_id)
    if target.exists():
        os.remove(target)
    return {"ok": True}
