import { useMemo, useState } from 'react';
import { SUPPORTED_LANGUAGES } from '../i18n';
import { WPM_MAX, WPM_MIN, WPM_STEP } from '../constants/reader';

const KEY = 'rsvp_settings_v1';
const DEFAULT_LANGUAGE = 'English';
const DEFAULT_WPM = 300;

function normalizeWpm(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return DEFAULT_WPM;
  const clamped = Math.max(WPM_MIN, Math.min(WPM_MAX, numeric));
  return Math.round(clamped / WPM_STEP) * WPM_STEP;
}

function normalizeLanguage(value) {
  if (SUPPORTED_LANGUAGES.includes(value)) return value;
  return DEFAULT_LANGUAGE;
}

function normalizeTranslateTarget(value) {
  if (SUPPORTED_LANGUAGES.includes(value)) return value;
  return 'English';
}

export const DEFAULT_SETTINGS = {
  wpm: DEFAULT_WPM,
  fontSize: 48,
  focusLetter: 2,
  orpColor: '#f25f4c',
  theme: 'dark',
  language: DEFAULT_LANGUAGE,
  translateTarget: 'English'
};

export function useSettings() {
  const [settings, setSettings] = useState(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return DEFAULT_SETTINGS;
      const parsed = { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
      return {
        ...parsed,
        wpm: normalizeWpm(parsed.wpm),
        language: normalizeLanguage(parsed.language),
        translateTarget: normalizeTranslateTarget(parsed.translateTarget)
      };
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const updateSettings = (patch) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      next.wpm = normalizeWpm(next.wpm);
      next.language = normalizeLanguage(next.language);
      next.translateTarget = normalizeTranslateTarget(next.translateTarget);
      localStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  };

  const resetSettings = () => {
    localStorage.removeItem(KEY);
    setSettings(DEFAULT_SETTINGS);
  };

  const isRTL = useMemo(() => false, []);

  return { settings, updateSettings, resetSettings, isRTL };
}
