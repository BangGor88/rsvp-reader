# API Reference

Base path: `/api`

## GET /health

Health check response:

```json
{
  "backend": "ok",
  "build": "RSVPReader-20260406-184446"
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

## GET /pdf/recent

Returns up to 5 recent books from the ebook library folder. Only books that are openable for RSVP reading are included.

## DELETE /pdf/{doc_id}

Clears cache entry and removes uploaded PDF file for the document ID.

## POST /pdf/models/open-folder

Opens the GGUF models folder in Windows Explorer. On desktop the folder is
`%LOCALAPPDATA%\RSVPReader\models` (created if it does not exist). The
"Open Models Folder" button on the upload page calls this endpoint.

Response:
```json
{ "ok": true, "path": "C:\\Users\\<user>\\AppData\\Local\\RSVPReader\\models" }
```

## POST /translate

Translate a sentence using the loaded GGUF model.

Request body:
```json
{
  "text": "The sentence to translate.",
  "target_language": "German",
  "focus_word": "sentence",
  "focus_word_index": 1,
  "highlight_focus": true
}
```

`target_language` must be one of: `English`, `German`, `French`, `Spanish`,
`Chinese`, `Japanese`, `Swedish`, `Indonesian`.

Response:
```json
{
  "translated": "Der [[[ Satz ]]] zum Übersetzen.",
  "translation_alternatives": ["Satz", "Phrase", "Aussage"]
}
```

`[[[` / `]]]` markers wrap the translated equivalent of the focus word.
Returns HTTP 503 if no model is loaded.