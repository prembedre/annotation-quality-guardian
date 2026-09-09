import React from 'react';

export function getScoreTier(score) {
  if (score == null) return 'unknown';
  if (score >= 85) return 'good';
  if (score >= 70) return 'medium';
  return 'risk';
}

export function getScoreTierLabel(score) {
  if (score == null) return 'N/A';
  if (score >= 85) return 'Good';
  if (score >= 70) return 'Medium';
  return 'High Risk';
}

export function ScoreIndicator({ trustScore, label = 'Trust Score' }) {
  if (trustScore == null) {
    return <span className="na-cell">—</span>;
  }

  const displayScore = Math.round(trustScore);
  const trustTier = getScoreTier(displayScore);

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', gap: '2px' }}>
      <span className={`score-pill ${trustTier}`}>
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: 'currentColor',
            display: 'inline-block',
          }}
        />
        <span className="mono-cell">{displayScore}%</span>
      </span>
      {label && label !== 'Trust Score' && (
        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
          {label}
        </span>
      )}
    </div>
  );
}

export default ScoreIndicator;