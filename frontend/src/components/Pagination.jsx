import React from 'react';

/**
 * Pagination component provides navigation and page size controls
 */
export function Pagination({
  currentPage,
  totalPages,
  totalRecords,
  pageSize,
  onPageChange,
  disabled = false,
}) {
  const startRecord = (currentPage - 1) * pageSize + 1;
  const endRecord = Math.min(currentPage * pageSize, totalRecords);

  return (
    <div className="pagination-bar">
      <div className="pagination-meta">
        Showing {startRecord} to {endRecord} of {totalRecords} records
      </div>
      <div className="pagination-controls">
        <button
          className="secondary-btn"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || disabled}
        >
          Previous
        </button>
        <span className="pagination-meta">
          Page {currentPage} of {totalPages}
        </span>
        <button
          className="secondary-btn"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || disabled}
        >
          Next
        </button>
      </div>
    </div>
  );
}
