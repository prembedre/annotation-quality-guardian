import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

/**
 * Modern pagination bar with records counter and previous/next page controls
 */
export function Pagination({
  currentPage,
  totalPages,
  totalRecords,
  pageSize,
  onPageChange,
  disabled = false,
}) {
  const startRecord = totalRecords === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endRecord = Math.min(currentPage * pageSize, totalRecords);

  return (
    <div className="pagination-bar">
      <div className="pagination-meta">
        Showing <strong style={{ color: 'var(--text-primary)' }}>{startRecord}</strong> to{' '}
        <strong style={{ color: 'var(--text-primary)' }}>{endRecord}</strong> of{' '}
        <strong style={{ color: 'var(--text-primary)' }}>{totalRecords}</strong> records
      </div>

      <div className="pagination-controls">
        <button
          type="button"
          className="secondary-btn"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1 || disabled}
          title="Previous Page"
        >
          <ChevronLeft size={14} />
          <span>Previous</span>
        </button>

        <span className="pagination-meta" style={{ padding: '0 0.5rem' }}>
          Page <strong style={{ color: 'var(--text-primary)' }}>{currentPage}</strong> of{' '}
          <strong style={{ color: 'var(--text-primary)' }}>{Math.max(totalPages, 1)}</strong>
        </span>

        <button
          type="button"
          className="secondary-btn"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || disabled}
          title="Next Page"
        >
          <span>Next</span>
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

export default Pagination;
