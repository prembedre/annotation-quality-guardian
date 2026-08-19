import React from 'react';

/**
 * LoadingState component displays a loading skeleton
 */
export function LoadingState() {
  return (
    <div className="loading-panel">
      <div style={{ width: '100%', maxWidth: '600px' }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="skeleton-row" />
        ))}
      </div>
    </div>
  );
}

/**
 * EmptyState component displays when no records match filters
 */
export function EmptyState({ message = 'No items match the selected filters.' }) {
  return (
    <div className="empty-state">
      <h3>No Results</h3>
      <p>{message}</p>
    </div>
  );
}

/**
 * ErrorState component displays error message with retry action
 */
export function ErrorState({ message, onRetry }) {
  return (
    <div className="message error">
      <div>
        <strong>Error:</strong> {message}
      </div>
      {onRetry && (
        <button className="inline-btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
