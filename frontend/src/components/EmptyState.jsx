import React from 'react';

/**
 * Reusable empty state component with Guardian iconography and optional CTA
 */
export function EmptyState({
  icon: Icon,
  title = 'No Data Available',
  description = 'There are no records to display at this moment.',
  action,
  actionLabel,
  onAction,
}) {
  return (
    <div className="empty-state">
      {Icon && (
        <div className="empty-state-icon">
          <Icon size={24} />
        </div>
      )}
      <h3>{title}</h3>
      <p>{description}</p>
      {actionLabel && onAction && (
        <button type="button" className="primary-btn" onClick={onAction}>
          {actionLabel}
        </button>
      )}
      {action && !actionLabel && action}
    </div>
  );
}

export default EmptyState;
