import React from 'react';
import { AlertOctagon, RotateCcw, FileSearch } from 'lucide-react';

/**
 * LoadingState displays animated skeleton placeholders
 */
export function LoadingState({ count = 5 }) {
  return (
    <div style={{ padding: '1rem 0', width: '100%' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-row" />
      ))}
    </div>
  );
}

/**
 * EmptyState displays when no records match or exist
 */
export function EmptyState({
  title = 'No Results Found',
  message = 'No items match the selected criteria or filters.',
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <FileSearch size={22} />
      </div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

/**
 * ErrorState displays error banner with an optional retry button
 */
export function ErrorState({ message, onRetry }) {
  return (
    <div className="alert" style={{ justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <AlertOctagon size={18} style={{ flexShrink: 0 }} />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          type="button"
          className="secondary-btn"
          onClick={onRetry}
          style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
        >
          <RotateCcw size={13} />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}

export default { LoadingState, EmptyState, ErrorState };
