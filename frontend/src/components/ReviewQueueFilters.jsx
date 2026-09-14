import React, { useState } from 'react';
import {
  Search,
  Filter,
  Layers,
  X,
  SlidersHorizontal,
  AlignJustify,
  List,
  Bookmark,
  Check,
} from 'lucide-react';

export function ReviewQueueFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  riskFilter,
  onRiskChange,
  pageSize,
  onPageSizeChange,
  onClearFilters,
  density = 'comfortable',
  onDensityChange,
  columns,
  onToggleColumn,
}) {
  const [columnMenuOpen, setColumnMenuOpen] = useState(false);
  const [savedViewsOpen, setSavedViewsOpen] = useState(false);

  const hasActiveFilters = Boolean(search || statusFilter !== 'all' || riskFilter !== 'all');

  const savedViews = [
    { name: 'All Review Items', status: 'all', risk: 'all' },
    { name: 'Needs Arbitration (Flagged)', status: 'flagged', risk: 'all' },
    { name: 'High Risk (Score < 70%)', status: 'all', risk: 'low' },
    { name: 'High Confidence Clean', status: 'not_flagged', risk: 'high' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginBottom: '1rem' }}>
      {/* Quick Saved Views Chips */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto', paddingBottom: '2px' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Bookmark size={12} />
          <span>Views:</span>
        </span>
        {savedViews.map((sv, idx) => {
          const isActive = statusFilter === sv.status && riskFilter === sv.risk;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => {
                onStatusChange(sv.status);
                onRiskChange(sv.risk);
              }}
              style={{
                background: isActive ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                border: `1px solid ${isActive ? 'var(--accent-brand)' : 'var(--border-subtle)'}`,
                color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                fontWeight: isActive ? 600 : 500,
                borderRadius: 'var(--radius-full)',
                padding: '2px 10px',
                fontSize: '0.72rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all var(--transition-fast)',
              }}
            >
              {sv.name}
            </button>
          );
        })}
      </div>

      {/* Main Filter Controls Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          padding: '0.65rem 0.85rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.65rem', flex: 1 }}>
          {/* Search Input */}
          <div style={{ position: 'relative', minWidth: '220px', flex: 1, maxWidth: '340px' }}>
            <Search
              size={13}
              style={{
                position: 'absolute',
                left: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
              }}
            />
            <input
              type="text"
              placeholder="Filter item ID, content, or label..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              style={{
                width: '100%',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.4rem 1.8rem 0.4rem 2rem',
                fontSize: '0.78rem',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
            {search && (
              <button
                type="button"
                onClick={() => onSearchChange('')}
                style={{
                  position: 'absolute',
                  right: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '2px',
                }}
              >
                <X size={12} />
              </button>
            )}
          </div>

          {/* Status Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <Filter size={12} />
            <select
              value={statusFilter}
              onChange={(e) => onStatusChange(e.target.value)}
              style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 0.6rem',
                color: 'var(--text-primary)',
                fontSize: '0.75rem',
              }}
            >
              <option value="all">All Statuses</option>
              <option value="flagged">Flagged Only</option>
              <option value="not_flagged">Not Flagged</option>
            </select>
          </div>

          {/* Risk Tier Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Tier:</span>
            <select
              value={riskFilter}
              onChange={(e) => onRiskChange(e.target.value)}
              style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 0.6rem',
                color: 'var(--text-primary)',
                fontSize: '0.75rem',
              }}
            >
              <option value="all">All Tiers</option>
              <option value="high">Good (85%+)</option>
              <option value="medium">Moderate (70–84%)</option>
              <option value="low">High Risk (&lt;70%)</option>
            </select>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              type="button"
              className="ghost-btn"
              onClick={onClearFilters}
              style={{ fontSize: '0.72rem', padding: '0.3rem 0.5rem' }}
            >
              <X size={12} />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* View Options: Density Toggle & Column Visibility */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {/* Density Toggle */}
          <div style={{ display: 'flex', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
            <button
              type="button"
              onClick={() => onDensityChange('comfortable')}
              style={{
                background: density === 'comfortable' ? 'var(--bg-surface-elevated)' : 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-xs)',
                padding: '3px 6px',
                cursor: 'pointer',
                color: density === 'comfortable' ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
              title="Comfortable row density"
            >
              <AlignJustify size={13} />
            </button>
            <button
              type="button"
              onClick={() => onDensityChange('compact')}
              style={{
                background: density === 'compact' ? 'var(--bg-surface-elevated)' : 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-xs)',
                padding: '3px 6px',
                cursor: 'pointer',
                color: density === 'compact' ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
              title="Compact row density"
            >
              <List size={13} />
            </button>
          </div>

          {/* Rows count selector */}
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.35rem 0.5rem',
              color: 'var(--text-primary)',
              fontSize: '0.75rem',
            }}
          >
            <option value={10}>10 rows</option>
            <option value={20}>20 rows</option>
            <option value={50}>50 rows</option>
          </select>
        </div>
      </div>
    </div>
  );
}

export default ReviewQueueFilters;
