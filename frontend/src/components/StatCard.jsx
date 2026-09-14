import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export function StatCard({
  label,
  value,
  icon: Icon,
  subtext,
  delta, // string '+4.2%' or object { value: '+4.2%', positive: true }
  sparkline = null, // array of numbers [30, 45, 60, 55, ...]
  statusType = 'neutral',
  statusLabel,
  loading = false,
  emptyMessage = 'Not enough data yet',
}) {
  const isValueEmpty = value == null || value === '—' || value === '' || value === 'N/A';

  // Helper to render inline SVG sparkline
  const renderSparkline = (points) => {
    if (!points || points.length < 2) return null;
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;
    const width = 64;
    const height = 22;

    const svgPoints = points
      .map((pt, i) => {
        const x = (i / (points.length - 1)) * width;
        const y = height - ((pt - min) / range) * (height - 4) - 2;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

    const strokeColor = delta && (typeof delta === 'object' ? !delta.positive : String(delta).startsWith('-'))
      ? 'var(--status-risk-solid)'
      : 'var(--status-good-solid)';

    return (
      <svg className="sparkline-svg" viewBox={`0 0 ${width} ${height}`}>
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={svgPoints}
        />
      </svg>
    );
  };

  const renderDelta = () => {
    if (!delta) return null;
    let text = delta;
    let isPos = true;

    if (typeof delta === 'object') {
      text = delta.value;
      isPos = delta.positive !== false;
    } else {
      isPos = !String(delta).startsWith('-');
    }

    return (
      <span className={`stat-card-delta ${isPos ? 'delta-positive' : 'delta-negative'}`}>
        {isPos ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
        <span>{text}</span>
      </span>
    );
  };

  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <span className="stat-card-label">{label}</span>
        {Icon && (
          <div className="stat-card-icon-wrap">
            <Icon size={15} />
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ margin: '0.5rem 0' }}>
          <div className="skeleton" style={{ height: '32px', width: '55%', marginBottom: '0.4rem' }} />
          <div className="skeleton" style={{ height: '14px', width: '80%' }} />
        </div>
      ) : isValueEmpty ? (
        <div style={{ margin: '0.2rem 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span
              style={{
                fontSize: '1.25rem',
                fontWeight: 600,
                color: 'var(--text-disabled)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              —
            </span>
            <div className="stat-empty-chart">
              <svg width="48" height="18" viewBox="0 0 48 18" fill="none">
                <path
                  d="M2 14L14 8L26 12L38 4L46 7"
                  stroke="var(--border-medium)"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                  strokeLinecap="round"
                />
              </svg>
              <span>Empty</span>
            </div>
          </div>
          <div className="stat-card-subtext" style={{ color: 'var(--text-muted)' }}>
            <span>{emptyMessage}</span>
          </div>
        </div>
      ) : (
        <>
          <div className="stat-card-value-row">
            <span className="stat-card-value">{value}</span>
            {renderDelta()}
          </div>

          <div className="stat-card-subtext">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {statusLabel && (
                <span className={`badge badge-${statusType}`}>
                  {statusLabel}
                </span>
              )}
              {subtext && <span>{subtext}</span>}
            </div>

            {sparkline && renderSparkline(sparkline)}
          </div>
        </>
      )}
    </div>
  );
}

export default StatCard;
