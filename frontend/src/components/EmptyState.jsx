import React from 'react';

export function EmptyState({
  icon: Icon,
  eyebrow,
  title = 'No Data Available',
  description = 'There are no records to display at this moment.',
  type = 'neutral',
  actionLabel,
  onAction,
  action,
  children,
}) {
  return (
    <div className="empty-state-card">
      <div className="empty-state-halo">
        {Icon ? (
          <Icon size={28} />
        ) : (
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="12" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" />
            <circle cx="16" cy="16" r="4" fill="currentColor" />
          </svg>
        )}
      </div>

      {eyebrow && <div className="eyebrow" style={{ marginBottom: '0.35rem' }}>{eyebrow}</div>}
      <h3 className="empty-state-title">{title}</h3>
      {description && <p className="empty-state-description">{description}</p>}

      {actionLabel && onAction && (
        <button
          type="button"
          className="primary-btn"
          onClick={onAction}
          style={{ marginBottom: children ? '1.5rem' : 0 }}
        >
          {actionLabel}
        </button>
      )}

      {action}
      {children}
    </div>
  );
}

export default EmptyState;
