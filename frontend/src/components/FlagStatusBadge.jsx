import React from 'react';

/**
 * FlagStatusBadge component displays flag status with styling based on status type
 */
export function FlagStatusBadge({ isFlagged }) {
  const status = isFlagged ? 'Flagged' : 'Not Flagged';
  const statusClass = isFlagged ? 'high-risk' : 'good';

  return (
    <span className={`status-badge ${statusClass}`}>
      {status}
    </span>
  );
}
