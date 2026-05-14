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

const DEFAULT_DAILY_GOAL = 10;

function normalizeGoal(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 1) return DEFAULT_DAILY_GOAL;
  return Math.min(Math.round(n), 180); // cap at 3 hours
}

export const DEFAULT_SETTINGS = {
  wpm: DEFAULT_WPM,
  fontSize: 48,
  focusLetter: 2,
  orpColor: '#f25f4c',
  theme: 'dark',
  language: DEFAULT_LANGUAGE,
  translateTarget: 'English',
  dailyGoalMinutes: DEFAULT_DAILY_GOAL
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
        translateTarget: normalizeTranslateTarget(parsed.translateTarget),
        dailyGoalMinutes: normalizeGoal(parsed.dailyGoalMinutes)
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
      next.dailyGoalMinutes = normalizeGoal(next.dailyGoalMinutes);
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
