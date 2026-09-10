import React from 'react';

/**
 * Reusable metric & stat tile component
 */
export function StatCard({
  label,
  value,
  icon: Icon,
  subtext,
  statusType = 'neutral',
  statusLabel,
  trend,
  loading = false,
}) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-label">{label}</span>
        {Icon && (
          <div className="stat-icon">
            <Icon size={16} />
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ margin: '0.4rem 0 0.6rem' }}>
          <div className="skeleton-row" style={{ height: '32px', width: '60%', marginBottom: '0.5rem' }} />
          <div className="skeleton-row" style={{ height: '14px', width: '85%' }} />
        </div>
      ) : (
        <>
          <div className="stat-value">{value}</div>

          {(subtext || statusLabel || trend) && (
            <div className="stat-subtext">
              {statusLabel && (
                <span className={`badge badge-${statusType}`}>
                  {statusLabel}
                </span>
              )}
              {trend && <span className="stat-trend">{trend}</span>}
              {subtext && <span>{subtext}</span>}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default StatCard;
