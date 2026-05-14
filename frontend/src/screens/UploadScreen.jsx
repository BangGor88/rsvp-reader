import { useEffect, useState } from 'react';
import { api } from '../api/client';
import ReadingStats from '../components/ReadingStats';
import { useReadingTimer } from '../hooks/useReadingTimer';

const PROGRESS_KEY_PREFIX = 'rsvp_progress_';

function getResumeIndex(docId) {
  try {
    const raw = localStorage.getItem(`${PROGRESS_KEY_PREFIX}${docId}`);
    if (!raw) return 0;
    const value = Number(raw);
    return Number.isFinite(value) && value >= 0 ? value : 0;
  } catch {
    return 0;
  }
}

export default function UploadScreen({ onUploaded, settings, t }) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [meta, setMeta] = useState(null);
  const [startPage, setStartPage] = useState(1);
  const [startWord, setStartWord] = useState(0);
  const [recentDocs, setRecentDocs] = useState([]);

  const loadRecentDocs = async () => {
    try {
      const res = await api.get('/pdf/recent');
      setRecentDocs(res.data.documents || []);
    } catch {
      setRecentDocs([]);
    }
  };

  useEffect(() => {
    loadRecentDocs();
  }, []);

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
      await loadRecentDocs();
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

  const openModelsFolder = async () => {
    setError('');
    try {
      await api.post('/pdf/models/open-folder');
    } catch (err) {
      const msg = err?.response?.data?.detail || t('upload.openModelsFailed');
      setError(String(msg));
    }
  };

  return (
    <div className="upload-screen">
      <h1>{t('upload.title')}</h1>
      <p>Rapid Serial Visual Presentation (RSVP)</p>
      <p>{t('upload.subtitle')}</p>

      <button type="button" onClick={openModelsFolder}>
        {t('upload.openModelsFolder')}
      </button>

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

      <div className="card">
        <h3>{t('stats.historyTitle')}</h3>
        <ReadingStatsInline settings={settings} t={t} />
      </div>

      <div className="card">
        <h3>{t('upload.recentTitle')}</h3>
        {recentDocs.length === 0 ? (
          <p>{t('upload.recentEmpty')}</p>
        ) : (
          <div className="recent-doc-list">
            {recentDocs.map((doc) => {
              const resumeIndex = getResumeIndex(doc.doc_id);
              return (
                <button
                  key={doc.doc_id}
                  className="recent-doc-item"
                  onClick={() =>
                    onUploaded({
                      docId: doc.doc_id,
                      pages: doc.pages || [],
                      startPage: 1,
                      startWord: 0,
                      resumeIndex,
                    })
                  }
                >
                  <strong>{doc.filename || doc.doc_id}</strong>
                  <span>
                    {doc.page_count} {t('upload.pages')} · {doc.word_count} {t('upload.words')}
                  </span>
                  {resumeIndex > 0 && (
                    <span>{t('upload.resumeFrom')} {resumeIndex + 1}</span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ReadingStatsInline({ settings, t }) {
  const goalMinutes = settings?.dailyGoalMinutes ?? 10;
  const { todaySeconds, goalSeconds, goalMet, history } = useReadingTimer(false, goalMinutes);
  return <ReadingStats todaySeconds={todaySeconds} goalSeconds={goalSeconds} goalMet={goalMet} history={history} inline t={t} />;
}
