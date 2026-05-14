import { useEffect, useState } from 'react';
import { SUPPORTED_LANGUAGES } from '../i18n';
import {
  FOCUS_LETTER_MAX,
  FOCUS_LETTER_MIN,
  WPM_MAX,
  WPM_MIN,
  WPM_STEP
} from '../constants/reader';

const colors = ['#f25f4c', '#ffd166', '#2ec4b6', '#e76f51', '#3a86ff'];
const fontSizeOptions = [16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 72, 80, 96];

export default function SettingsPanel({ open, settings, onUpdate, onReset, onClose, t }) {
  const [pendingLanguage, setPendingLanguage] = useState(settings.language);

  useEffect(() => {
    if (open) setPendingLanguage(settings.language);
  }, [open, settings.language]);

  if (!open) return null;

  return (
    <aside className="drawer">
      <div className="drawer-head">
        <h3>{t('settings.title')}</h3>
        <button onClick={onClose}>{t('settings.close')}</button>
      </div>

      <label>{t('settings.wpm')}: {settings.wpm}</label>
      <div className="row">
        <button onClick={() => onUpdate({ wpm: Math.max(WPM_MIN, settings.wpm - WPM_STEP) })}>-20</button>
        <div className="control-meta">{settings.wpm} {t('control.wpm')}</div>
        <button onClick={() => onUpdate({ wpm: Math.min(WPM_MAX, settings.wpm + WPM_STEP) })}>+20</button>
      </div>

      <label>{t('settings.fontSize')}: {settings.fontSize}px</label>
      <select
        value={settings.fontSize}
        onChange={(e) => onUpdate({ fontSize: Number(e.target.value) })}
      >
        {fontSizeOptions.map((size) => (
          <option key={size} value={size}>
            {size}px
          </option>
        ))}
      </select>

      <label>{t('settings.focusLetter')}: {settings.focusLetter}</label>
      <div className="grid-5">
        {Array.from(
          { length: FOCUS_LETTER_MAX - FOCUS_LETTER_MIN + 1 },
          (_, i) => FOCUS_LETTER_MIN + i
        ).map((num) => (
          <button
            key={num}
            onClick={() => onUpdate({ focusLetter: num })}
            style={{
              fontWeight: settings.focusLetter === num ? '700' : '400',
              opacity: settings.focusLetter === num ? 1 : 0.6
            }}
          >
            {num}
          </button>
        ))}
      </div>

      <label>{t('settings.orpColor')}</label>
      <div className="swatches">
        {colors.map((c) => (
          <button
            key={c}
            className="swatch"
            style={{ backgroundColor: c }}
            onClick={() => onUpdate({ orpColor: c })}
            aria-label={`Color ${c}`}
          />
        ))}
      </div>

      <label>{t('settings.theme')}</label>
      <div className="row">
        <button onClick={() => onUpdate({ theme: 'light' })}>{t('settings.light')}</button>
        <button onClick={() => onUpdate({ theme: 'dark' })}>{t('settings.dark')}</button>
      </div>

      <label>{t('settings.language')}</label>
      <select
        value={pendingLanguage}
        onChange={(e) => setPendingLanguage(e.target.value)}
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang} value={lang}>
            {lang}
          </option>
        ))}
      </select>

      <button
        onClick={() => onUpdate({ language: pendingLanguage })}
        disabled={pendingLanguage === settings.language}
      >
        {t('settings.applyLanguage')}
      </button>

      <label>{t('settings.dailyGoal')}: {settings.dailyGoalMinutes} {t('settings.minutes')}</label>
      <div className="row">
        <button
          onClick={() => onUpdate({ dailyGoalMinutes: Math.max(1, settings.dailyGoalMinutes - 5) })}
          disabled={settings.dailyGoalMinutes <= 1}
        >-5</button>
        <div className="control-meta">{settings.dailyGoalMinutes} {t('settings.minutes')}</div>
        <button onClick={() => onUpdate({ dailyGoalMinutes: Math.min(180, settings.dailyGoalMinutes + 5) })}>+5</button>
      </div>

      <button onClick={onReset}>{t('settings.reset')}</button>
    </aside>
  );
}
