import React from 'react';

/**
 * Reusable empty state component with Guardian iconography and optional CTA.
 * type: 'neutral' (indigo - setup needed) | 'success' (green - all caught up) | 'warning'
 */
export function EmptyState({
  icon: Icon,
  title = 'No Data Available',
  description = 'There are no records to display at this moment.',
  type = 'neutral',
  action,
  actionLabel,
  onAction,
  children,
}) {
  const iconClass = `empty-state-icon ${type}`;

  return (
    <div className="empty-state">
      {Icon && (
        <div className={iconClass}>
          <Icon size={26} />
        </div>
      )}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {children}
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
