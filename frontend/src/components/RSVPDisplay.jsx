import { useMemo, useRef } from 'react';
import { FOCUS_LETTER_MAX, FOCUS_LETTER_MIN } from '../constants/reader';

export default function RSVPDisplay({
  word,
  fontSize,
  color,
  isRTL = false,
  focusLetter,
  showSentenceContext = true,
  originalSentence = '',
  translatedSentence = '',
  translationAlternatives = [],
  translationAlternativesLabel = 'Possible translations'
}) {
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

  const normalizedFocus = useMemo(
    () => (word || '').replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, ''),
    [word]
  );

  const originalSentenceParts = useMemo(() => {
    if (!originalSentence || !normalizedFocus) {
      return [{ text: originalSentence, highlight: false }];
    }

    const escaped = normalizedFocus.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escaped})`, 'iu');
    const match = regex.exec(originalSentence);
    if (!match) {
      return [{ text: originalSentence, highlight: false }];
    }

    const start = match.index;
    const end = start + match[0].length;
    return [
      { text: originalSentence.slice(0, start), highlight: false },
      { text: originalSentence.slice(start, end), highlight: true },
      { text: originalSentence.slice(end), highlight: false },
    ];
  }, [originalSentence, normalizedFocus]);

  const translatedSentenceParts = useMemo(() => {
    if (!translatedSentence) {
      return [{ text: translatedSentence, highlight: false }];
    }

    const markerMatch = translatedSentence.match(/\[\[\[(.*?)\]\]\]|\[\[(.*?)\]\]/s);
    if (!markerMatch) {
      return [{ text: translatedSentence, highlight: false }];
    }

    const highlightedText = markerMatch[1] || markerMatch[2] || '';
    const beforeText = translatedSentence.slice(0, markerMatch.index);
    const afterText = translatedSentence.slice(markerMatch.index + markerMatch[0].length);
    return [
      { text: beforeText, highlight: false },
      { text: highlightedText, highlight: true },
      { text: afterText, highlight: false },
    ];
  }, [translatedSentence]);

  return (
    <div className="rsvp-stack" dir={isRTL ? 'rtl' : 'ltr'}>
      <div className="rsvp-shell" style={{ fontSize, transform: `translateX(${-shiftPx}px)` }}>
        <span className="rsvp-before">{before}</span>
        <span className="rsvp-orp" style={{ color }}>{orp}</span>
        <span className="rsvp-after">{after}</span>
      </div>
      {showSentenceContext && originalSentence && (
        <div className="rsvp-context">
          <div className="rsvp-translation">
            {originalSentenceParts.map((part, index) => (
              <span key={`orig-${index}`} className={part.highlight ? 'rsvp-highlight' : ''}>{part.text}</span>
            ))}
          </div>
          {translatedSentence && (
            <>
              <div className="rsvp-translation rsvp-translation-result">
                {translatedSentenceParts.map((part, index) => (
                  <span key={`trans-${index}`} className={part.highlight ? 'rsvp-highlight' : ''}>{part.text}</span>
                ))}
              </div>
              {translationAlternatives.length > 0 && (
                <div className="rsvp-translation-options" aria-label={translationAlternativesLabel}>
                  <span className="rsvp-translation-options-label">{translationAlternativesLabel}:</span>{' '}
                  {translationAlternatives.join(', ')}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
