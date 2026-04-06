import { useMemo, useRef } from 'react';
import { FOCUS_LETTER_MAX, FOCUS_LETTER_MIN } from '../constants/reader';

export default function RSVPDisplay({ word, fontSize, color, isRTL = false, focusLetter }) {
  const safeWord = word || '';
  const fallbackLetter = 3;
  const rawLetter = Number.isFinite(focusLetter) ? focusLetter : fallbackLetter;
  const clampedLetter = Math.max(FOCUS_LETTER_MIN, Math.min(FOCUS_LETTER_MAX, rawLetter));
  const orpIndex = safeWord.length
    ? Math.min(safeWord.length - 1, Math.max(0, clampedLetter - 1))
    : 0;
  const before = safeWord.slice(0, orpIndex);
  const orp = safeWord[orpIndex] || '';
  const after = safeWord.slice(orpIndex + 1);

  const canvasRef = useRef(null);
  const shiftPx = useMemo(() => {
    if (typeof document === 'undefined') return 0;
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return 0;

    ctx.font = `700 ${fontSize}px Space Grotesk, Segoe UI, sans-serif`;
    const beforeWidth = ctx.measureText(before).width;
    const orpWidth = ctx.measureText(orp || '').width;

    return beforeWidth + (orpWidth / 2);
  }, [before, orp, fontSize]);

  return (
    <div
      className="rsvp-shell"
      dir={isRTL ? 'rtl' : 'ltr'}
      style={{ fontSize, transform: `translateX(${-shiftPx}px)` }}
    >
      <span className="rsvp-before">{before}</span>
      <span className="rsvp-orp" style={{ color }}>{orp}</span>
      <span className="rsvp-after">{after}</span>
    </div>
  );
}
