import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import ControlBar from '../components/ControlBar';
import ProgressBar from '../components/ProgressBar';
import RSVPDisplay from '../components/RSVPDisplay';
import SettingsPanel from '../components/SettingsPanel';
import { useRSVP } from '../hooks/useRSVP';
import { WPM_MAX, WPM_MIN, WPM_STEP } from '../constants/reader';

function findStartIndex(pages, pageNum, fallbackWord) {
  if (!pages || !pages.length) return Math.max(0, fallbackWord || 0);
  const p = pages.find((x) => x.page === pageNum);
  if (p) return p.start_word;
  return Math.max(0, fallbackWord || 0);
}

export default function ReaderScreen({ docId, startPage, startWord, settings, onSettings, onResetSettings, isRTL, onUploadNew, t }) {
  const [words, setWords] = useState([]);
  const [pages, setPages] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    api.get(`/pdf/words/${docId}`).then((res) => {
      setWords(res.data.words || []);
      setPages(res.data.pages || []);
    });
  }, [docId]);

  const initialIndex = useMemo(
    () => findStartIndex(pages, startPage, startWord),
    [pages, startPage, startWord]
  );

  const stageX = Number.isFinite(settings?.position?.x) ? settings.position.x : 50;
  const stageY = Number.isFinite(settings?.position?.y) ? settings.position.y : 50;
  const focusLetter = Number.isFinite(settings?.focusLetter) ? settings.focusLetter : 2;

  const rsvp = useRSVP(words, settings.wpm, initialIndex);

  useEffect(() => {
    rsvp.setWpm(settings.wpm);
  }, [settings.wpm, rsvp]);

  const decreaseWpm = () => onSettings({ wpm: Math.max(WPM_MIN, settings.wpm - WPM_STEP) });
  const increaseWpm = () => onSettings({ wpm: Math.min(WPM_MAX, settings.wpm + WPM_STEP) });

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === ' ') {
        e.preventDefault();
        rsvp.isPlaying ? rsvp.pause() : rsvp.play();
      } else if (e.key === 'ArrowLeft') {
        rsvp.seek(rsvp.currentIndex - 10);
      } else if (e.key === 'ArrowRight') {
        rsvp.seek(rsvp.currentIndex + 10);
      } else if (e.key === 'ArrowUp') {
        increaseWpm();
      } else if (e.key === 'ArrowDown') {
        decreaseWpm();
      } else if (e.key === 'Escape') {
        setSettingsOpen(false);
      } else if (e.key === '?') {
        setShowShortcuts((v) => !v);
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [rsvp, settings.wpm, onSettings]);

  return (
    <div className="reader-screen">
      <ProgressBar currentIndex={rsvp.currentIndex} totalWords={rsvp.totalWords} />

      <header className="top-actions">
        <button onClick={onUploadNew}>{t('reader.uploadNew')}</button>
        <div className="row">
          <button onClick={() => setSettingsOpen(true)}>{t('reader.settings')}</button>
        </div>
      </header>

      <div
        className="reader-stage"
        style={{
          left: `${stageX}vw`,
          top: `${stageY}vh`
        }}
      >
        <RSVPDisplay
          word={rsvp.currentWord}
          fontSize={settings.fontSize}
          color={settings.orpColor}
          isRTL={isRTL}
          focusLetter={focusLetter}
        />
      </div>

      <ControlBar
        isPlaying={rsvp.isPlaying}
        onPlayPause={() => (rsvp.isPlaying ? rsvp.pause() : rsvp.play())}
        onBack={() => rsvp.seek(rsvp.currentIndex - 10)}
        onForward={() => rsvp.seek(rsvp.currentIndex + 10)}
        onWpmDown={decreaseWpm}
        onWpmUp={increaseWpm}
        currentIndex={rsvp.currentIndex}
        totalWords={rsvp.totalWords}
        onSeek={rsvp.seek}
        wpm={settings.wpm}
        t={t}
      />

      <SettingsPanel
        open={settingsOpen}
        settings={settings}
        onUpdate={onSettings}
        onReset={onResetSettings}
        onClose={() => setSettingsOpen(false)}
        t={t}
      />

      {showShortcuts && (
        <div className="overlay" onClick={() => setShowShortcuts(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{t('reader.shortcuts')}</h3>
            <p>{t('reader.shortcut.space')}</p>
            <p>{t('reader.shortcut.arrows')}</p>
            <p>{t('reader.shortcut.wpm')}</p>
            <p>{t('reader.shortcut.escape')}</p>
            <p>{t('reader.shortcut.help')}</p>
          </div>
        </div>
      )}
    </div>
  );
}
