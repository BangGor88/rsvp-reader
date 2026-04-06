export default function ProgressBar({ currentIndex, totalWords }) {
  const pct = totalWords > 0 ? (currentIndex / Math.max(1, totalWords - 1)) * 100 : 0;
  return (
    <div className="progress-wrap" aria-hidden="true">
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}
