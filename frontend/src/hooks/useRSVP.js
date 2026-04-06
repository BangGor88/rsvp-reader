import { useCallback, useEffect, useMemo, useState } from 'react';
import { WPM_MIN } from '../constants/reader';

export function useRSVP(words, initialWpm = 300, initialIndex = 0) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [wpm, setWpm] = useState(initialWpm);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    setCurrentIndex(initialIndex || 0);
  }, [initialIndex, words]);

  useEffect(() => {
    if (!isPlaying || words.length === 0) return;

    const intervalMs = Math.max(WPM_MIN, Math.round(60000 / Math.max(1, wpm)));
    const id = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= words.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [isPlaying, wpm, words.length]);

  const currentWord = useMemo(() => words[currentIndex] || '', [words, currentIndex]);

  const seek = useCallback((index) => {
    if (!words.length) return;
    const clamped = Math.max(0, Math.min(words.length - 1, index));
    setCurrentIndex(clamped);
  }, [words.length]);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);

  return {
    currentWord,
    currentIndex,
    totalWords: words.length,
    isPlaying,
    wpm,
    play,
    pause,
    seek,
    setWpm
  };
}
