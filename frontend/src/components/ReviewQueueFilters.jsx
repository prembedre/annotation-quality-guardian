import React from 'react';
import { Search, Filter, Layers, X } from 'lucide-react';

/**
 * Compact horizontal filter bar for Review Queue
 */
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
}) {
  const hasActiveFilters = Boolean(
    search || statusFilter !== 'all' || riskFilter !== 'all'
  );

  return (
    <div className="review-filters-bar">
      <div className="toolbar">
        {/* Search Field */}
        <div
          className="toolbar-field"
          style={{
            position: 'relative',
            flex: '1 1 240px',
            maxWidth: '360px',
          }}
        >
          <Search
            size={14}
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
            id="search"
            type="text"
            placeholder="Search item ID or text..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{ paddingLeft: '32px' }}
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
              title="Clear search"
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Flag Status */}
        <div className="toolbar-field">
          <label htmlFor="statusFilter">
            <Filter size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Flag:
          </label>
          <select
            id="statusFilter"
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            <option value="all">All Flags</option>
            <option value="flagged">Flagged Only</option>
            <option value="not_flagged">Not Flagged</option>
          </select>
        </div>

        {/* Quality Tier */}
        <div className="toolbar-field">
          <label htmlFor="riskFilter">Tier:</label>
          <select
            id="riskFilter"
            value={riskFilter}
            onChange={(e) => onRiskChange(e.target.value)}
          >
            <option value="all">All Tiers</option>
            <option value="high">Good (85%+)</option>
            <option value="medium">Medium (70–84%)</option>
            <option value="low">High Risk (&lt;70%)</option>
          </select>
        </div>

        {/* Rows per page */}
        <div className="toolbar-field">
          <label htmlFor="pageSize">
            <Layers size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Rows:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            style={{ minWidth: '75px' }}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>

        {/* Clear Filters Action */}
        <div className="toolbar-actions">
          {hasActiveFilters && (
            <button
              type="button"
              className="secondary-btn"
              onClick={onClearFilters}
              style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
            >
              <X size={13} />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReviewQueueFilters;
