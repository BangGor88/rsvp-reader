# Troubleshooting

## Notes and Limitations

- Text extraction quality depends on PDF content and encoding.
- Image-only PDFs are detected heuristically (`image_only` flag), and extraction may be incomplete.
- In-memory document cache is process-local; restarting backend clears cache.

## Common Issues

### 422 Only PDF files are supported

Ensure uploaded file has a `.pdf` extension.

### Unable to parse PDF

File may be corrupted, encrypted, or not text-extractable.

### Frontend cannot reach backend

- Confirm backend is running on port `8000`.
- Confirm CORS via `ALLOWED_ORIGINS` when using non-default frontend ports.

### Desktop app fails to launch UI

Ensure `backend/static/index.html` exists in packaged assets (handled by build script).