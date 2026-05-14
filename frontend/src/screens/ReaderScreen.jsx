import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api/client';
import ControlBar from '../components/ControlBar';
import ProgressBar from '../components/ProgressBar';
import RSVPDisplay from '../components/RSVPDisplay';
import ReadingStats from '../components/ReadingStats';
import SettingsPanel from '../components/SettingsPanel';
import { useRSVP } from '../hooks/useRSVP';
import { useReadingTimer } from '../hooks/useReadingTimer';
import { WPM_MAX, WPM_MIN, WPM_STEP } from '../constants/reader';

const CONTROL_TRANSLATE_LANGUAGES = ['English', 'Swedish', 'Indonesian', 'German', 'Japanese', 'Spanish'];
const FIXED_STAGE_X = 20;
const FIXED_STAGE_Y = 50;

function normalizeWord(word) {
  return (word || '').replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '');
}

function isSentenceEnd(token) {
  if (!token) return false;
  return /[.!?。！？]["')\]]*$/.test(token);
}

function sentenceFromWords(words, index) {
  if (!words.length || index < 0 || index >= words.length) {
    return { text: '', start: -1, end: -1 };
  }

  let start = index;
  while (start > 0 && !isSentenceEnd(words[start - 1])) {
    start -= 1;
  }

  let end = index;
  while (end < words.length - 1 && !isSentenceEnd(words[end])) {
    end += 1;
  }

  return {
    text: words.slice(start, end + 1).join(' ').trim(),
    start,
    end,
  };
}

function findStartIndex(pages, pageNum, fallbackWord) {
  if (!pages || !pages.length) return Math.max(0, fallbackWord || 0);
  const p = pages.find((x) => x.page === pageNum);
  if (p) return p.start_word;
  return Math.max(0, fallbackWord || 0);
}

export default function ReaderScreen({ docId, startPage, startWord, resumeIndex, settings, onSettings, onResetSettings, isRTL, onUploadNew, t }) {
  const [words, setWords] = useState([]);
  const [pages, setPages] = useState([]);
  const [originalSentence, setOriginalSentence] = useState('');
  const [translatedSentence, setTranslatedSentence] = useState('');
  const [translationAlternatives, setTranslationAlternatives] = useState([]);
  const [translatingWord, setTranslatingWord] = useState(false);
  const [hasTranslationResult, setHasTranslationResult] = useState(false);
  const [translationError, setTranslationError] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showSentenceContext, setShowSentenceContext] = useState(true);
  const activeSentenceRef = useRef('');
  const progressKey = `rsvp_progress_${docId}`;

  useEffect(() => {
    api.get(`/pdf/words/${docId}`).then((res) => {
      setWords(res.data.words || []);
      setPages(res.data.pages || []);
    });
  }, [docId]);

  const initialIndex = useMemo(
    () => (Number.isInteger(resumeIndex) ? resumeIndex : findStartIndex(pages, startPage, startWord)),
    [pages, startPage, startWord, resumeIndex]
  );

  const focusLetter = Number.isFinite(settings?.focusLetter) ? settings.focusLetter : 2;

  const rsvp = useRSVP(words, settings.wpm, initialIndex);
  const currentWord = rsvp.currentWord || '';

  const { todaySeconds, goalSeconds, goalMet, history: readingHistory } =
    useReadingTimer(rsvp.isPlaying, settings.dailyGoalMinutes ?? 10);

  useEffect(() => {
    try {
      localStorage.setItem(progressKey, String(rsvp.currentIndex));
    } catch {
    }
  }, [progressKey, rsvp.currentIndex]);

  useEffect(() => {
    setOriginalSentence('');
    setTranslatedSentence('');
    setTranslationAlternatives([]);
    setHasTranslationResult(false);
    setTranslatingWord(false);
    setTranslationError('');
  }, [currentWord]);

  useEffect(() => {
    rsvp.setWpm(settings.wpm);
  }, [settings.wpm, rsvp]);

  const decreaseWpm = () => onSettings({ wpm: Math.max(WPM_MIN, settings.wpm - WPM_STEP) });
  const increaseWpm = () => onSettings({ wpm: Math.min(WPM_MAX, settings.wpm + WPM_STEP) });

  const translateCurrentWord = async () => {
    if (!currentWord.trim()) return;

    const sentenceContext = sentenceFromWords(words, rsvp.currentIndex);
    if (!sentenceContext.text) return;

    const focusWordIndex = Math.max(0, rsvp.currentIndex - sentenceContext.start);

    const sourceSentence = sentenceContext.text;
    activeSentenceRef.current = sourceSentence;
    setOriginalSentence(sourceSentence);
    setTranslatedSentence('');
    setTranslationAlternatives([]);
    setHasTranslationResult(false);
    setTranslatingWord(true);
    setTranslationError('');

    try {
      const res = await api.post('/translate', {
        text: sourceSentence,
        target_language: settings.translateTarget,
        focus_word: normalizeWord(currentWord),
        focus_word_index: focusWordIndex,
        highlight_focus: true,
      });

      if (activeSentenceRef.current !== sourceSentence) return;
      const translated = (res.data.translated || '').trim();
      const alternatives = Array.isArray(res.data.translation_alternatives)
        ? res.data.translation_alternatives.slice(0, 5).filter((item) => typeof item === 'string' && item.trim())
        : [];
      setTranslatedSentence(translated);
      setTranslationAlternatives(alternatives);
      setHasTranslationResult(Boolean(translated));
    } catch (err) {
      if (activeSentenceRef.current !== sourceSentence) return;
      setTranslatedSentence('');
      setTranslationAlternatives([]);
      const detail = err?.response?.data?.detail;
      setTranslationError(detail ? String(detail) : t('translate.error'));
    } finally {
      if (activeSentenceRef.current === sourceSentence) {
        setTranslatingWord(false);
      }
    }
  };

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

      <ReadingStats
        todaySeconds={todaySeconds}
        goalSeconds={goalSeconds}
        goalMet={goalMet}
        history={readingHistory}
        t={t}
      />

      {translatingWord && (
        <div className="notice" style={{ textAlign: 'center', padding: '4px 0' }}>
          {t('translate.loading')}
        </div>
      )}

      {translationError && (
        <div className="notice error" style={{ textAlign: 'center', padding: '4px 0' }}>
          {translationError}
        </div>
      )}

      <header className="top-actions">
        <button onClick={onUploadNew}>{t('reader.uploadNew')}</button>
        <div className="row">
          <button onClick={() => setSettingsOpen(true)}>{t('reader.settings')}</button>
        </div>
      </header>

      <div
        className="reader-stage"
        style={{
          left: `${FIXED_STAGE_X}vw`,
          top: `${FIXED_STAGE_Y}vh`
        }}
      >
        <RSVPDisplay
          word={currentWord}
          fontSize={settings.fontSize}
          color={settings.orpColor}
          isRTL={isRTL}
          focusLetter={focusLetter}
          showSentenceContext={showSentenceContext}
          originalSentence={originalSentence}
          translatedSentence={translatedSentence}
          translationAlternatives={translationAlternatives}
          translationAlternativesLabel={t('translate.alternatives')}
        />
      </div>

      <ControlBar
        isPlaying={rsvp.isPlaying}
        onPlayPause={() => (rsvp.isPlaying ? rsvp.pause() : rsvp.play())}
        onTranslateWord={translateCurrentWord}
        onToggleSentenceContext={() => setShowSentenceContext((prev) => !prev)}
        showSentenceContext={showSentenceContext}
        canToggleSentenceContext={hasTranslationResult}
        onTranslateTargetChange={(language) => onSettings({ translateTarget: language })}
        translateTarget={CONTROL_TRANSLATE_LANGUAGES.includes(settings.translateTarget) ? settings.translateTarget : 'English'}
        translateLanguages={CONTROL_TRANSLATE_LANGUAGES}
        isTranslatingWord={translatingWord}
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
