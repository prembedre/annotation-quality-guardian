import React from 'react';

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  children,
}) {
  return (
    <div className="page-header">
      <div className="page-header-content">
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>

      {(actions || children) && (
        <div className="page-header-actions">
          {actions}
          {children}
        </div>
      )}
    </div>
  );
}

export default PageHeader;
