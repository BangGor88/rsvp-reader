import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Make backend modules importable when tests are run from repository root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routers import pdf  # noqa: E402


class RecentDocumentTests(unittest.TestCase):
    def test_recent_docs_are_limited_to_five_and_keep_filenames(self):
        original_upload_dir = pdf.UPLOAD_DIR
        original_library_dir = pdf.EBOOK_LIBRARY_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf.UPLOAD_DIR = temp_path
            pdf.EBOOK_LIBRARY_DIR = temp_path
            try:
                for index in range(6):
                    doc_id = f"doc-{index}"
                    (temp_path / f"{doc_id}.pdf").write_bytes(b"%PDF-1.4 dummy")
                    meta = {
                        "doc_id": doc_id,
                        "filename": f"book-{index}.pdf",
                        "uploaded_at": f"2026-05-14T00:00:0{index}Z",
                        "word_count": 10 + index,
                        "page_count": 1 + index,
                        "image_only": False,
                    }
                    (temp_path / f"{doc_id}.json").write_text(json.dumps(meta), encoding="utf-8")
                    time.sleep(0.01)

                docs = pdf._list_recent_docs()

                self.assertEqual(len(docs), 5)
                self.assertEqual(docs[0]["filename"], "book-5.pdf")
                self.assertEqual(docs[-1]["filename"], "book-1.pdf")
                self.assertTrue(all(doc["filename"].startswith("book-") for doc in docs))
            finally:
                pdf.UPLOAD_DIR = original_upload_dir
                pdf.EBOOK_LIBRARY_DIR = original_library_dir

    def test_uuid_filename_falls_back_to_pdf_title(self):
        original_upload_dir = pdf.UPLOAD_DIR
        original_library_dir = pdf.EBOOK_LIBRARY_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf.UPLOAD_DIR = temp_path
            pdf.EBOOK_LIBRARY_DIR = temp_path
            try:
                doc_id = "ffef2238-f437-48e1-b6fe-012af2ff1b7b"
                (temp_path / f"{doc_id}.pdf").write_bytes(b"%PDF-1.4 dummy")
                meta = {
                    "doc_id": doc_id,
                    "filename": f"{doc_id}.pdf",
                    "uploaded_at": "2026-05-14T00:00:00Z",
                    "word_count": 10,
                    "page_count": 1,
                    "image_only": False,
                }
                (temp_path / f"{doc_id}.json").write_text(json.dumps(meta), encoding="utf-8")

                with patch("routers.pdf._title_from_pdf", return_value="Readable Title"):
                    record = pdf._read_doc_meta(doc_id)

                self.assertIsNotNone(record)
                self.assertEqual(record["filename"], "Readable Title.pdf")
            finally:
                pdf.UPLOAD_DIR = original_upload_dir
                pdf.EBOOK_LIBRARY_DIR = original_library_dir

    def test_recent_docs_only_include_openable_books(self):
        original_upload_dir = pdf.UPLOAD_DIR
        original_library_dir = pdf.EBOOK_LIBRARY_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf.UPLOAD_DIR = temp_path
            pdf.EBOOK_LIBRARY_DIR = temp_path
            try:
                open_doc_id = "doc-open"
                blocked_doc_id = "doc-locked"
                (temp_path / f"{open_doc_id}.pdf").write_bytes(b"%PDF-1.4 dummy")
                (temp_path / f"{blocked_doc_id}.pdf").write_bytes(b"%PDF-1.4 dummy")

                open_meta = {
                    "doc_id": open_doc_id,
                    "filename": "readable.pdf",
                    "uploaded_at": "2026-05-14T00:00:00Z",
                    "word_count": 120,
                    "page_count": 2,
                    "image_only": False,
                }
                blocked_meta = {
                    "doc_id": blocked_doc_id,
                    "filename": "image-only.pdf",
                    "uploaded_at": "2026-05-14T00:00:01Z",
                    "word_count": 0,
                    "page_count": 2,
                    "image_only": True,
                }
                (temp_path / f"{open_doc_id}.json").write_text(json.dumps(open_meta), encoding="utf-8")
                (temp_path / f"{blocked_doc_id}.json").write_text(json.dumps(blocked_meta), encoding="utf-8")

                docs = pdf._list_recent_docs()
                doc_ids = [doc["doc_id"] for doc in docs]

                self.assertIn(open_doc_id, doc_ids)
                self.assertNotIn(blocked_doc_id, doc_ids)
            finally:
                pdf.UPLOAD_DIR = original_upload_dir
                pdf.EBOOK_LIBRARY_DIR = original_library_dir


if __name__ == "__main__":
    unittest.main()