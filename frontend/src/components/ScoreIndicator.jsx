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

/**
 * ScoreIndicator component displays trust scores
 * with visual indicators based on score tiers
 */
export function ScoreIndicator({ trustScore }) {
  // Assuming trustScore is passed as 0-100 percentage.
  const displayScore = trustScore != null ? Math.round(trustScore) : null;
  const trustTier = getScoreTier(displayScore);

  return (
    <div className="score-group">
      <div>
        <span className={`score-pill ${trustTier}`}>
          {displayScore != null ? displayScore : 'N/A'}
        </span>
        <div className="score-meta">Trust Score</div>
      </div>
    </div>
  );
}
