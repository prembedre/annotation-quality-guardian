import React from 'react';

/**
 * ReviewQueueFilters component provides search and filtering capabilities
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
  const hasActiveFilters = search || statusFilter !== 'all' || riskFilter !== 'all';

  return (
    <div className="filters-panel">
      <div className="toolbar">
        <div className="toolbar-field">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            placeholder="Item ID or Content"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        <div className="toolbar-field">
          <label htmlFor="statusFilter">Flag Status</label>
          <select
            id="statusFilter"
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            <option value="all">All</option>
            <option value="flagged">Flagged</option>
            <option value="not_flagged">Not Flagged</option>
          </select>
        </div>

        <div className="toolbar-field">
          <label htmlFor="riskFilter">Quality Tier</label>
          <select
            id="riskFilter"
            value={riskFilter}
            onChange={(e) => onRiskChange(e.target.value)}
          >
            <option value="all">All</option>
            <option value="high">Good (85+)</option>
            <option value="medium">Medium (70-84)</option>
            <option value="low">High Risk (Below 70)</option>
          </select>
        </div>

        <div className="toolbar-field">
          <label htmlFor="pageSize">Rows per page</label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>

        <div className="toolbar-actions">
          {hasActiveFilters && (
            <button className="secondary-btn" onClick={onClearFilters}>
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
