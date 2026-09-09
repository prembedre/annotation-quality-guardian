import React, { useEffect, useState, useCallback } from 'react';
import { ReviewQueueHeader } from '../components/ReviewQueueHeader';
import { ReviewQueueFilters } from '../components/ReviewQueueFilters';
import { ReviewQueueTable } from '../components/ReviewQueueTable';
import { Pagination } from '../components/Pagination';
import { DatasetExport } from '../components/DatasetExport';
import { ErrorState } from '../components/States';
import { Toast } from '../components/Toast';
import {
  getReviewQueue,
  exportReviewQueue,
  resolveReviewItem,
} from '../services/reviewQueueService';

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

  const currentProjectId = 1;

  /**
   * Fetch review queue data
   */
  const fetchQueue = useCallback(
    async (
      currentPage = 1,
      currentPageSize = pageSize,
      currentStatus = statusFilter,
      currentSearch = search,
      currentRisk = riskFilter
    ) => {
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

        setQueueData(data || []);
        setTotal(pagination?.total || 0);
        setTotalPages(pagination?.totalPages || 1);
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

  useEffect(() => {
    fetchQueue(1, pageSize, statusFilter, search, riskFilter);
  }, []);

  useEffect(() => {
    setPage(1);
    fetchQueue(1, pageSize, statusFilter, search, riskFilter);
  }, [statusFilter, search, riskFilter]);

  const handlePageSizeChange = useCallback(
    (newPageSize) => {
      setPageSize(newPageSize);
      setPage(1);
      fetchQueue(1, newPageSize, statusFilter, search, riskFilter);
    },
    [statusFilter, search, riskFilter, fetchQueue]
  );

  const handlePageChange = useCallback(
    (newPage) => {
      const safePage = Math.min(Math.max(1, newPage), totalPages);
      fetchQueue(safePage, pageSize, statusFilter, search, riskFilter);
    },
    [pageSize, statusFilter, search, riskFilter, totalPages, fetchQueue]
  );

  const handleSearchChange = useCallback((value) => {
    setSearch(value);
    setPage(1);
  }, []);

  const handleStatusChange = useCallback((value) => {
    setStatusFilter(value);
    setPage(1);
  }, []);

  const handleRiskChange = useCallback((value) => {
    setRiskFilter(value);
    setPage(1);
  }, []);

  const handleClearFilters = useCallback(() => {
    setSearch('');
    setStatusFilter('all');
    setRiskFilter('all');
    setPage(1);
    fetchQueue(1, pageSize, 'all', '', 'all');
  }, [pageSize, fetchQueue]);

  const handleResolve = useCallback(
    async (itemId, payload) => {
      try {
        setToastMessage('');
        const result = await resolveReviewItem(itemId, payload);
        setToastType('success');
        setToastMessage(result?.message || 'Review item resolved successfully.');

        await fetchQueue(page, pageSize, statusFilter, search, riskFilter);
      } catch (resolveError) {
        console.error('Failed to resolve review item:', resolveError);
        setToastType('error');
        setToastMessage(
          resolveError.response?.data?.detail ||
            resolveError.message ||
            'Failed to resolve review item.'
        );
      }
    },
    [fetchQueue, page, pageSize, statusFilter, search, riskFilter]
  );

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
      } catch (exportError) {
        setToastType('error');
        setToastMessage(
          exportError.message || `Failed to export as ${format.toUpperCase()}.`
        );
      }
    },
    [currentProjectId]
  );

  const handleRetry = useCallback(() => {
    fetchQueue(page, pageSize, statusFilter, search, riskFilter);
  }, [page, pageSize, statusFilter, search, riskFilter, fetchQueue]);

  return (
    <div>
      {/* Header with integrated export action */}
      <div className="page-header">
        <ReviewQueueHeader />

        <div className="export-actions">
          <DatasetExport onExport={handleExport} disabled={loading} />
        </div>
      </div>

      {/* Compact Horizontal Filter Bar */}
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

      {/* Dense Results Table */}
      <ReviewQueueTable
        items={queueData}
        loading={loading}
        onResolve={handleResolve}
      />

      {/* Pagination */}
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

      {/* Toast Feedback */}
      <Toast
        message={toastMessage}
        type={toastType}
        onClose={() => setToastMessage('')}
        duration={4000}
      />
    </div>
  );
}