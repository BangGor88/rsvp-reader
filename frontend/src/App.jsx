import { useEffect, useState } from 'react';
import ReaderScreen from './screens/ReaderScreen';
import UploadScreen from './screens/UploadScreen';
import { useSettings } from './hooks/useSettings';
import { api } from './api/client';
import { createTranslator } from './i18n';

export default function App() {
  const [docState, setDocState] = useState(null);
  const [health, setHealth] = useState({ backend: 'unknown', build: 'unknown' });
  const [aiStatus, setAiStatus] = useState('unknown');
  const [canExitApp, setCanExitApp] = useState(false);
  const [appExitState, setAppExitState] = useState('idle');
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

  useEffect(() => {
    const checkAI = () => {
      api.get('/ai/status')
        .then((res) => setAiStatus(res.data.status))
        .catch(() => setAiStatus('unknown'));
    };
    checkAI();
    const id = setInterval(checkAI, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    api.get('/app/status')
      .then((res) => setCanExitApp(Boolean(res.data?.canExit)))
      .catch(() => setCanExitApp(false));
  }, []);

  const pillClass = (value) => {
    if (value === 'ok') return 'pill green';
    if (value === 'unknown') return 'pill amber';
    return 'pill red';
  };

  const aiPillClass = (value) => {
    if (value === 'online') return 'pill green';
    if (value === 'offline') return 'pill red';
    return 'pill amber';
  };

  const handleAIToggle = () => {
    if (aiStatus === 'online') {
      api.post('/ai/stop').then(() => setAiStatus('offline')).catch(() => {});
    } else if (aiStatus === 'offline') {
      setAiStatus('loading');
      api.post('/ai/start').then(() => setAiStatus('loading')).catch(() => setAiStatus('offline'));
    }
  };

  const handleExitApp = () => {
    if (!canExitApp || appExitState === 'exiting') return;
    setAppExitState('exiting');
    api.post('/app/exit')
      .catch(() => setAppExitState('failed'));
  };

  return (
    <div className="app-shell">
      <div className="health-bar">
        <button className={pillClass(health.backend)} title={t('health.fixBackend')}>{t('health.backend')}: {t(`status.${health.backend}`)}</button>
        <button
          className={aiPillClass(aiStatus)}
          title={aiStatus === 'online' ? t('health.aiStop') : t('health.aiStart')}
          onClick={handleAIToggle}
          disabled={aiStatus === 'loading' || aiStatus === 'unknown'}
        >
          {t('health.ai')}: {t(`status.${aiStatus}`)}
        </button>
        <button className="pill" title={t('health.buildTitle')}>{t('health.build')}: {health.build || t('status.unknown')}</button>
        {canExitApp && (
          <button
            className={appExitState === 'failed' ? 'pill red' : 'pill'}
            title={t('health.exitAppTitle')}
            onClick={handleExitApp}
            disabled={appExitState === 'exiting'}
          >
            {appExitState === 'exiting' ? t('health.exiting') : t('health.exitApp')}
          </button>
        )}
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
