import React, { useEffect, useState, useCallback } from 'react';
import { ReviewQueueHeader } from '../components/ReviewQueueHeader';
import { ReviewQueueFilters } from '../components/ReviewQueueFilters';
import { ReviewQueueTable } from '../components/ReviewQueueTable';
import { Pagination } from '../components/Pagination';
import { DatasetExport } from '../components/DatasetExport';
import { ErrorState } from '../components/States';
import { Toast } from '../components/Toast';
import { getReviewQueue, exportReviewQueue } from '../services/reviewQueueService';

export default function ReviewQueue() {
  const [queueData, setQueueData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');
  
  // Using a default project ID for now. Ideally this would come from a context or URL param.
  const currentProjectId = 1;

  /**
   * Fetch review queue data
   */
  const fetchQueue = useCallback(
    async (currentPage = 1, currentPageSize = pageSize, currentStatus = statusFilter, currentSearch = search, currentRisk = riskFilter) => {
      try {
        setLoading(true);
        setError('');

        const result = await getReviewQueue({
          page: currentPage,
          pageSize: currentPageSize,
          status: currentStatus,
          search: currentSearch,
          riskFilter: currentRisk,
          projectId: currentProjectId,
        });

        const { data, pagination } = result;
        setQueueData(data);
        setTotal(pagination.total);
        setTotalPages(pagination.totalPages);
        setPage(currentPage);
      } catch (fetchError) {
        setError(fetchError.message || 'Unable to load the review queue.');
        setQueueData([]);
      } finally {
        setLoading(false);
      }
    },
    [pageSize, statusFilter, search, riskFilter, currentProjectId]
  );

  /**
   * Initial load
   */
  useEffect(() => {
    fetchQueue(1, pageSize, statusFilter, search, riskFilter);
  }, []);

  /**
   * Handle filter changes - reset to page 1
   */
  useEffect(() => {
    setPage(1);
    fetchQueue(1, pageSize, statusFilter, search, riskFilter);
  }, [statusFilter, search, riskFilter]);

  /**
   * Handle page size changes
   */
  const handlePageSizeChange = useCallback((newPageSize) => {
    setPageSize(newPageSize);
    setPage(1);
    fetchQueue(1, newPageSize, statusFilter, search, riskFilter);
  }, [statusFilter, search, riskFilter, fetchQueue]);

  /**
   * Handle page changes
   */
  const handlePageChange = useCallback((newPage) => {
    const safePage = Math.min(Math.max(1, newPage), totalPages);
    fetchQueue(safePage, pageSize, statusFilter, search, riskFilter);
  }, [pageSize, statusFilter, search, riskFilter, totalPages, fetchQueue]);

  /**
   * Handle search changes
   */
  const handleSearchChange = useCallback((value) => {
    setSearch(value);
    setPage(1);
  }, []);

  /**
   * Handle status filter changes
   */
  const handleStatusChange = useCallback((value) => {
    setStatusFilter(value);
    setPage(1);
  }, []);

  /**
   * Handle risk filter changes
   */
  const handleRiskChange = useCallback((value) => {
    setRiskFilter(value);
    setPage(1);
  }, []);

  /**
   * Clear all filters
   */
  const handleClearFilters = useCallback(() => {
    setSearch('');
    setStatusFilter('all');
    setRiskFilter('all');
    setPage(1);
    fetchQueue(1, pageSize, 'all', '', 'all');
  }, [pageSize, fetchQueue]);

  /**
   * Handle dataset export
   */
  const handleExport = useCallback(
    async (format) => {
      try {
        const blob = await exportReviewQueue(currentProjectId, format);

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `aqg-project-${currentProjectId}.${format}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

        setToastType('success');
        setToastMessage(`Dataset exported as ${format.toUpperCase()} successfully!`);
        // The toast will automatically hide itself based on duration prop
      } catch (exportError) {
        setToastType('error');
        setToastMessage(exportError.message || `Failed to export as ${format.toUpperCase()}.`);
      }
    },
    [currentProjectId]
  );

  /**
   * Handle retry after error
   */
  const handleRetry = useCallback(() => {
    fetchQueue(page, pageSize, statusFilter, search, riskFilter);
  }, [page, pageSize, statusFilter, search, riskFilter, fetchQueue]);

  return (
    <div className="page-shell">
      <div className="page-header">
        <ReviewQueueHeader />
        <div className="export-actions">
          <DatasetExport onExport={handleExport} disabled={loading} />
        </div>
      </div>

      <ReviewQueueFilters
        search={search}
        onSearchChange={handleSearchChange}
        statusFilter={statusFilter}
        onStatusChange={handleStatusChange}
        riskFilter={riskFilter}
        onRiskChange={handleRiskChange}
        pageSize={pageSize}
        onPageSizeChange={handlePageSizeChange}
        onClearFilters={handleClearFilters}
      />

      {error && <ErrorState message={error} onRetry={handleRetry} />}

      <ReviewQueueTable items={queueData} loading={loading} />

      {!loading && !error && queueData.length > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalRecords={total}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          disabled={loading}
        />
      )}

      <Toast
        message={toastMessage}
        type={toastType}
        onClose={() => setToastMessage('')}
        duration={4000}
      />
    </div>
  );
}
