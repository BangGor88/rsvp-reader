import os
import json
import uuid
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile

from services.pdf_service import parse_pdf

router = APIRouter(prefix="/pdf", tags=["pdf"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path.cwd() / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EBOOK_LIBRARY_DIR = Path(
    os.getenv("EBOOK_LIBRARY_DIR", str(UPLOAD_DIR / "ebooks"))
)
EBOOK_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)


def _default_models_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / "RSVPReader" / "models"

    user_profile = os.getenv("USERPROFILE", "").strip()
    if user_profile:
        return Path(user_profile) / "AppData" / "Local" / "RSVPReader" / "models"

    return Path.cwd() / "models"


MODELS_DIR = Path(os.getenv("MODELS_DIR", str(_default_models_dir())))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

META_SUFFIX = ".json"

ParsedDocument = dict[str, Any]
pdf_cache: dict[str, ParsedDocument] = {}

UUID_FILENAME_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.pdf$"
)


def _migrate_legacy_uploads() -> None:
    if EBOOK_LIBRARY_DIR.resolve() == UPLOAD_DIR.resolve():
        return

    for ext in ("*.pdf", f"*{META_SUFFIX}"):
        for legacy_file in UPLOAD_DIR.glob(ext):
            target = EBOOK_LIBRARY_DIR / legacy_file.name
            if target.exists():
                continue
            try:
                legacy_file.replace(target)
            except Exception:
                continue


_migrate_legacy_uploads()


def _doc_path(doc_id: str) -> Path:
    return EBOOK_LIBRARY_DIR / f"{doc_id}.pdf"


def _meta_path(doc_id: str) -> Path:
    return EBOOK_LIBRARY_DIR / f"{doc_id}{META_SUFFIX}"


def _title_from_pdf(pdf_path: Path) -> str | None:
    try:
        doc = fitz.open(str(pdf_path))
    except Exception:
        return None

    try:
        title = (doc.metadata or {}).get("title") or ""
        title = title.strip()
        if title:
            return title

        page_text = ""
        if len(doc):
            page_text = (doc[0].get_text("text") or "").strip()
        if not page_text:
            return None

        first_line = page_text.splitlines()[0].strip()
        if first_line:
            return first_line[:120]
        return None
    finally:
        doc.close()


def _display_filename(meta: dict[str, Any], pdf_path: Path) -> str:
    stored_name = str(meta.get("filename") or "").strip()
    if stored_name and not UUID_FILENAME_RE.match(stored_name):
        return stored_name

    inferred = _title_from_pdf(pdf_path)
    if inferred:
        safe = re.sub(r"[\\/:*?\"<>|]+", " ", inferred).strip()
        safe = re.sub(r"\s+", " ", safe)
        if safe:
            return f"{safe}.pdf"

    if stored_name:
        return stored_name

    return f"{pdf_path.stem}.pdf"


def _doc_meta_payload(doc_id: str, filename: str, parsed: ParsedDocument) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "filename": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "word_count": parsed["word_count"],
        "page_count": parsed["page_count"],
        "image_only": parsed["image_only"],
    }


def _write_doc_meta(doc_id: str, filename: str, parsed: ParsedDocument) -> dict[str, Any]:
    payload = _doc_meta_payload(doc_id, filename, parsed)
    _meta_path(doc_id).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def _read_doc_meta(doc_id: str) -> dict[str, Any] | None:
    meta_file = _meta_path(doc_id)
    if meta_file.exists():
        try:
            payload = json.loads(meta_file.read_text(encoding="utf-8"))
            pdf_file = _doc_path(doc_id)
            if pdf_file.exists():
                payload["filename"] = _display_filename(payload, pdf_file)
            return payload
        except Exception:
            return None
    pdf_file = _doc_path(doc_id)
    if not pdf_file.exists():
        return None

    try:
        parsed = parse_pdf(str(pdf_file))
    except Exception:
        return None

    payload = {
        "doc_id": doc_id,
        "filename": _display_filename({"filename": f"{doc_id}.pdf"}, pdf_file),
        "uploaded_at": None,
        "word_count": parsed["word_count"],
        "page_count": parsed["page_count"],
        "image_only": parsed["image_only"],
    }
    try:
        _meta_path(doc_id).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return payload


def _list_recent_docs() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for pdf_file in sorted(EBOOK_LIBRARY_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
        doc_id = pdf_file.stem
        meta = _read_doc_meta(doc_id)
        if not meta:
            continue

        # Show only books that can be opened for RSVP reading.
        word_count = int(meta.get("word_count") or 0)
        if word_count <= 0:
            continue

        docs.append(meta)
    return docs[:5]


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
    _write_doc_meta(doc_id, filename, parsed)
    return _public_doc_payload(doc_id, parsed)


@router.get("/recent")
def recent_uploads():
    return {"documents": _list_recent_docs()}


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
    meta = _meta_path(doc_id)
    if meta.exists():
        os.remove(meta)
    return {"ok": True}


@router.post("/models/open-folder")
def open_models_folder():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if sys.platform.startswith("win"):
            os.startfile(str(MODELS_DIR))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(MODELS_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(MODELS_DIR)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open models folder: {exc}") from exc

    return {"ok": True, "path": str(MODELS_DIR)}
