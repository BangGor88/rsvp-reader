# API Reference

Base path: `/api`

## GET /health

Health check response:

```json
{
  "backend": "ok"
}
```

## POST /pdf/upload

Upload a PDF as `multipart/form-data` field `file`.

Response shape:

```json
{
  "doc_id": "uuid",
  "word_count": 1234,
  "page_count": 12,
  "pages": [
    { "page": 1, "start_word": 0, "end_word": 103 }
  ],
  "image_only": false
}
```

## GET /pdf/words/{doc_id}

Returns parsed words and page ranges for a document.

## DELETE /pdf/{doc_id}

Clears cache entry and removes uploaded PDF file for the document ID.