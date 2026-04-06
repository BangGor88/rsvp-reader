import { useState } from 'react';
import { api } from '../api/client';

export default function UploadScreen({ onUploaded, t }) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [meta, setMeta] = useState(null);
  const [startPage, setStartPage] = useState(1);
  const [startWord, setStartWord] = useState(0);

  const uploadFile = async (file) => {
    setError('');
    const form = new FormData();
    form.append('file', file);

    try {
      const res = await api.post('/pdf/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMeta(res.data);
      setStartPage(1);
      setStartWord(0);
    } catch (err) {
      const msg = err?.response?.data?.detail || t('upload.failed');
      setError(String(msg));
    }
  };

  const onDrop = async (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) await uploadFile(file);
  };

  return (
    <div className="upload-screen">
      <h1>{t('upload.title')}</h1>
      <p>{t('upload.subtitle')}</p>

      <label
        className={`drop-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
          }}
        />
        <span>{t('upload.dropzone')}</span>
      </label>

      {error && <div className="notice error">{error}</div>}

      {meta && (
        <div className="card">
          <p>{t('upload.words')}: {meta.word_count}</p>
          <p>{t('upload.pages')}: {meta.page_count}</p>
          {meta.image_only && (
            <div className="notice warning">{t('upload.imageOnly')}</div>
          )}

          <div className="row">
            <label>{t('upload.startPage')}</label>
            <input
              type="number"
              min={1}
              max={Math.max(1, meta.page_count)}
              value={startPage}
              onChange={(e) => setStartPage(Number(e.target.value))}
            />
          </div>

          <div className="row">
            <label>{t('upload.startWord')}</label>
            <input
              type="number"
              min={0}
              max={Math.max(0, meta.word_count - 1)}
              value={startWord}
              onChange={(e) => setStartWord(Number(e.target.value))}
            />
          </div>

          <button
            onClick={() =>
              onUploaded({
                docId: meta.doc_id,
                pages: meta.pages,
                startPage,
                startWord
              })
            }
          >
            {t('upload.startReading')}
          </button>
        </div>
      )}
    </div>
  );
}
