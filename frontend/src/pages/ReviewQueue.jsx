import React, { useEffect, useState, useCallback } from 'react';
import { PageHeader } from '../components/PageHeader';
import { ReviewQueueFilters } from '../components/ReviewQueueFilters';
import { ReviewQueueTable } from '../components/ReviewQueueTable';
import { Pagination } from '../components/Pagination';
import { DatasetExport } from '../components/DatasetExport';
import { ErrorState, EmptyState, LoadingState } from '../components/States';
import { useToast } from '../components/ToastContext';
import { useProject } from '../components/ProjectContext';
import {
  getReviewQueue,
  exportReviewQueue,
  resolveReviewItem,
} from '../services/reviewQueueService';
import { CheckSquare, RefreshCw } from 'lucide-react';

export default function ReviewQueue() {
  const { projectId: currentProjectId } = useProject();
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
  const [density, setDensity] = useState('comfortable');

  const { success, error: toastError } = useToast();

  const fetchQueue = useCallback(
    async (
      currentPage = 1,
      currentPageSize = pageSize,
      currentStatus = statusFilter,
      currentSearch = search,
      currentRisk = riskFilter
    ) => {
      if (!currentProjectId) {
        setQueueData([]);
        setTotal(0);
        setTotalPages(1);
        setLoading(false);
        return;
      }
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

  const handleClearFilters = useCallback(() => {
    setSearch('');
    setStatusFilter('all');
    setRiskFilter('all');
    setPage(1);
  }, []);

  const handleExport = useCallback(
    async (format) => {
      try {
        const blobData = await exportReviewQueue(currentProjectId, format);
        const mimeType = format === 'json' ? 'application/json' : 'text/csv';
        const blob = blobData instanceof Blob ? blobData : new Blob([blobData], { type: mimeType });
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `project_${currentProjectId}_review_export.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);

        success(`Successfully generated and downloaded ${format.toUpperCase()} export!`);
      } catch (exportErr) {
        console.error('Export failed:', exportErr);
        const msg = exportErr?.response?.data?.detail || 'Failed to export dataset. Please try again.';
        toastError(msg);
      }
    },
    [currentProjectId, success, toastError]
  );

  const handleResolve = useCallback(
    async (itemId, resolution) => {
      try {
        await resolveReviewItem(itemId, resolution);
        const actionLabel =
          resolution.action === 'confirm'
            ? 'confirmed'
            : resolution.action === 'correct'
            ? 'corrected'
            : 'escalated';

        success(`Item #${itemId} successfully ${actionLabel}!`);
        await fetchQueue(page, pageSize, statusFilter, search, riskFilter);
      } catch (actionErr) {
        console.error('Resolution failed:', actionErr);
        toastError(actionErr.message || `Failed to update item #${itemId}.`);
        throw actionErr;
      }
    },
    [fetchQueue, page, pageSize, statusFilter, search, riskFilter, success, toastError]
  );

  if (!currentProjectId) {
    return (
      <div>
        <PageHeader
          eyebrow="Data-Grid Observability"
          title="Review Queue"
          subtitle="Active flagged annotations, dispute triage, and auditor escalation actions."
        />
        <EmptyState
          title="No Project Selected"
          description="Please select or create a project from the sidebar to inspect items in the review queue."
        />
      </div>
    );
  }

  return (
    <div>
      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Data-Grid Observability"
        title="Review Queue"
        subtitle="Active flagged annotations, dispute triage, and auditor escalation actions."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => fetchQueue(page, pageSize, statusFilter, search, riskFilter)}
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>

            <DatasetExport
              onExport={handleExport}
              disabled={loading || total === 0}
              totalCount={total}
              flaggedCount={queueData.filter((i) => i.flagged).length}
            />
          </div>
        }
      />

      {error && (
        <ErrorState
          message={error}
          onRetry={() => fetchQueue(page, pageSize, statusFilter, search, riskFilter)}
        />
      )}

      {/* Advanced Filter Toolbar with Density and Saved Views */}
      <ReviewQueueFilters
        search={search}
        onSearchChange={handleSearchChange}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        riskFilter={riskFilter}
        onRiskChange={setRiskFilter}
        pageSize={pageSize}
        onPageSizeChange={handlePageSizeChange}
        onClearFilters={handleClearFilters}
        density={density}
        onDensityChange={setDensity}
      />

      {/* Main Review Queue Table Card */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '1.5rem' }}>
            <LoadingState count={5} />
          </div>
        ) : queueData.length === 0 ? (
          <div style={{ padding: '2rem' }}>
            <EmptyState
              icon={CheckSquare}
              title="All Items Caught Up"
              description="No annotation items match your current review criteria or need resolution."
            />
          </div>
        ) : (
          <>
            <ReviewQueueTable
              items={queueData}
              loading={loading}
              onResolve={handleResolve}
              density={density}
            />

            {/* Pagination Controls */}
            <div
              style={{
                padding: '0.75rem 1rem',
                borderTop: '1px solid var(--border-subtle)',
                background: 'var(--bg-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Showing <strong className="font-mono">{queueData.length}</strong> of{' '}
                <strong className="font-mono">{total}</strong> total review records
              </span>

              <Pagination
                page={page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                disabled={loading}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}