import { useEffect, useRef, useState } from 'react';

const HISTORY_KEY = 'rsvp_history_v1';
const FLUSH_INTERVAL_MS = 10_000; // save to localStorage every 10s while playing

function todayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveHistory(history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch {
    // quota exceeded — ignore
  }
}

/** Returns the last N calendar dates (descending, today first) as YYYY-MM-DD strings. */
function lastNDates(n) {
  const dates = [];
  for (let i = 0; i < n; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    dates.push(
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    );
  }
  return dates;
}

/** Format seconds → "m:ss" or "Xm Ys" label */
export function formatSeconds(secs) {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/**
 * Tracks daily reading time.
 * @param {boolean} isPlaying  — mirror of RSVP play state
 * @param {number}  goalMinutes — daily goal in minutes (from settings)
 */
export function useReadingTimer(isPlaying, goalMinutes = 10) {
  const [todaySeconds, setTodaySeconds] = useState(() => {
    const h = loadHistory();
    return h[todayKey()] || 0;
  });

  // Accumulated seconds since last flush (not yet written to localStorage)
  const pendingRef = useRef(0);
  const flushTimer = useRef(null);
  const tickTimer = useRef(null);

  // Flush pending seconds to localStorage
  const flush = () => {
    if (pendingRef.current === 0) return;
    const key = todayKey();
    const history = loadHistory();
    history[key] = (history[key] || 0) + pendingRef.current;
    saveHistory(history);
    setTodaySeconds(history[key]);
    pendingRef.current = 0;
  };

  useEffect(() => {
    if (isPlaying) {
      // Tick every second
      tickTimer.current = setInterval(() => {
        pendingRef.current += 1;
        setTodaySeconds((prev) => prev + 1);
      }, 1000);

      // Flush to localStorage every 10s
      flushTimer.current = setInterval(flush, FLUSH_INTERVAL_MS);
    } else {
      // Stop ticking and flush on pause
      clearInterval(tickTimer.current);
      clearInterval(flushTimer.current);
      flush();
    }

    return () => {
      clearInterval(tickTimer.current);
      clearInterval(flushTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPlaying]);

  // Flush on unmount
  useEffect(() => () => flush(), []); // eslint-disable-line react-hooks/exhaustive-deps

  const goalSeconds = goalMinutes * 60;
  const goalMet = todaySeconds >= goalSeconds;

  /** Last 10 days (descending) with seconds and labels */
  const history = lastNDates(10).map((date) => {
    const stored = loadHistory();
    return {
      date,
      seconds: stored[date] || 0,
      label: date.slice(5), // "MM-DD"
    };
  });

  return { todaySeconds, goalSeconds, goalMet, history };
}
