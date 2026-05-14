import { useState } from 'react';
import { formatSeconds } from '../hooks/useReadingTimer';

export default function ReadingStats({ todaySeconds, goalSeconds, goalMet, history, t }) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const pct = goalSeconds > 0 ? Math.min(1, todaySeconds / goalSeconds) : 0;
  const maxSeconds = Math.max(...history.map((d) => d.seconds), goalSeconds, 1);

  return (
    <>
      {/* Compact strip in reader */}
      <div className="reading-stats-strip" title={t('stats.stripTitle')}>
        <span className="stats-label">
          {goalMet ? '★ ' : ''}{formatSeconds(todaySeconds)} / {formatSeconds(goalSeconds)}
        </span>
        <div className="stats-bar-track" onClick={() => setHistoryOpen(true)} title={t('stats.viewHistory')}>
          <div
            className="stats-bar-fill"
            style={{
              width: `${Math.round(pct * 100)}%`,
              background: goalMet ? '#2ec4b6' : '#f25f4c',
            }}
          />
        </div>
        <button className="stats-history-btn" onClick={() => setHistoryOpen(true)}>
          {t('stats.history')}
        </button>
      </div>

      {/* History modal */}
      {historyOpen && (
        <div className="overlay" onClick={() => setHistoryOpen(false)}>
          <div className="modal stats-modal" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-head">
              <h3>{t('stats.historyTitle')}</h3>
              <button onClick={() => setHistoryOpen(false)}>✕</button>
            </div>

            {/* Goal line note */}
            <p className="stats-goal-note">
              {t('stats.dailyGoal')}: <strong>{formatSeconds(goalSeconds)}</strong>
              {' '}{goalMet ? '✓' : ''}
            </p>

            {/* Bar chart — oldest on left */}
            <div className="stats-chart">
              {[...history].reverse().map(({ date, seconds, label }) => {
                const barPct = seconds / maxSeconds;
                const isToday = date === history[0].date;
                const metGoal = seconds >= goalSeconds;
                return (
                  <div key={date} className="stats-col">
                    <div className="stats-bar-outer">
                      <div
                        className="stats-bar-inner"
                        style={{
                          height: `${Math.round(barPct * 100)}%`,
                          background: metGoal ? '#2ec4b6' : isToday ? '#f25f4c' : 'rgba(255,255,255,0.3)',
                        }}
                        title={`${label}: ${formatSeconds(seconds)}`}
                      />
                    </div>
                    <span className="stats-day-label" style={{ fontWeight: isToday ? 700 : 400 }}>
                      {isToday ? t('stats.today') : label}
                    </span>
                    <span className="stats-day-time">{seconds > 0 ? formatSeconds(seconds) : '—'}</span>
                  </div>
                );
              })}
            </div>

            {/* Totals row */}
            <div className="stats-summary row">
              <span>{t('stats.total10days')}: <strong>{formatSeconds(history.reduce((a, d) => a + d.seconds, 0))}</strong></span>
              <span>{t('stats.daysGoalMet')}: <strong>{history.filter((d) => d.seconds >= goalSeconds).length} / 10</strong></span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
