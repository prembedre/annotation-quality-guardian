import React from 'react';
import { Flag, CheckCircle2 } from 'lucide-react';

/**
 * FlagStatusBadge component displays item flag status with refined styling
 */
export function FlagStatusBadge({ isFlagged }) {
  if (isFlagged) {
    return (
      <span className="status-badge high-risk">
        <Flag size={12} style={{ flexShrink: 0 }} />
        <span>Flagged</span>
      </span>
    );
  }

  return (
    <span className="status-badge good">
      <CheckCircle2 size={12} style={{ flexShrink: 0 }} />
      <span>Clear</span>
    </span>
  );
}

export default FlagStatusBadge;
