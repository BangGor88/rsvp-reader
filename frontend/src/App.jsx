import { useEffect, useState } from 'react';
import ReaderScreen from './screens/ReaderScreen';
import UploadScreen from './screens/UploadScreen';
import { useSettings } from './hooks/useSettings';
import { api } from './api/client';
import { createTranslator } from './i18n';

export default function App() {
  const [docState, setDocState] = useState(null);
  const [health, setHealth] = useState({ backend: 'unknown', build: 'unknown' });
  const { settings, updateSettings, resetSettings, isRTL } = useSettings();
  const t = createTranslator(settings.language);

  useEffect(() => {
    document.body.dataset.theme = settings.theme;
  }, [settings.theme]);

  useEffect(() => {
    const id = setInterval(() => {
      api.get('/health').then((res) => setHealth(res.data)).catch(() => {
        setHealth({ backend: 'unavailable', build: 'unavailable' });
      });
    }, 3000);

    return () => clearInterval(id);
  }, []);

  const pillClass = (value) => {
    if (value === 'ok') return 'pill green';
    if (value === 'unknown') return 'pill amber';
    return 'pill red';
  };

  return (
    <div className="app-shell">
      <div className="health-bar">
        <button className={pillClass(health.backend)} title={t('health.fixBackend')}>{t('health.backend')}: {t(`status.${health.backend}`)}</button>
        <button className="pill" title={t('health.buildTitle')}>{t('health.build')}: {health.build || t('status.unknown')}</button>
      </div>

      {docState ? (
        <ReaderScreen
          docId={docState.docId}
          startPage={docState.startPage}
          startWord={docState.startWord}
          resumeIndex={docState.resumeIndex}
          settings={settings}
          onSettings={updateSettings}
          onResetSettings={resetSettings}
          isRTL={isRTL}
          t={t}
          onUploadNew={async () => {
            setDocState(null);
          }}
        />
      ) : (
        <UploadScreen onUploaded={setDocState} settings={settings} t={t} />
      )}
    </div>
  );
}
