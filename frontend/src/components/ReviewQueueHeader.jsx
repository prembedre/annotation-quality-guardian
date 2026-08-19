import React from 'react';

/**
 * ReviewQueueHeader component displays the page title and description
 */
export function ReviewQueueHeader() {
  return (
    <div className="topbar">
      <div>
        <p className="eyebrow">Data Quality Guardian</p>
        <h1>Review Queue</h1>
        <p className="subtitle">Review flagged annotations and resolve quality issues.</p>
      </div>
    </div>
  );
}
