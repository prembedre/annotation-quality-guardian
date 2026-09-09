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
    </div>
  );
}

export default StatCard;
