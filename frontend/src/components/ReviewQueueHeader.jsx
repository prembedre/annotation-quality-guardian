import React from 'react';

/**
 * ReviewQueueHeader component displays the title and subtitle
 */
export function ReviewQueueHeader() {
  return (
    <div>
      <h1 className="page-title">Review Queue</h1>
      <p className="page-subtitle">
        Review flagged annotations, investigate quality anomalies, and submit reviewer resolutions.
      </p>
    </div>
  );
}

export default ReviewQueueHeader;
