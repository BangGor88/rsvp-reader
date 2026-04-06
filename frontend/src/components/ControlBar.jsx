export default function ControlBar({
  isPlaying,
  onPlayPause,
  onBack,
  onForward,
  onWpmDown,
  onWpmUp,
  currentIndex,
  totalWords,
  onSeek,
  wpm,
  t
}) {
  return (
    <div className="control-bar">
      <button onClick={onPlayPause}>{isPlaying ? t('control.pause') : t('control.play')}</button>
      <button onClick={onBack}>{t('control.back10')}</button>
      <button onClick={onForward}>{t('control.forward10')}</button>
      <div className="control-meta">{currentIndex + 1} / {Math.max(1, totalWords)}</div>
      <input
        type="range"
        min={0}
        max={Math.max(0, totalWords - 1)}
        value={Math.min(currentIndex, Math.max(0, totalWords - 1))}
        onChange={(e) => onSeek(Number(e.target.value))}
      />
      <div className="row">
        <button onClick={onWpmDown}>-20</button>
        <div className="control-meta">{wpm} {t('control.wpm')}</div>
        <button onClick={onWpmUp}>+20</button>
      </div>
    </div>
  );
}
