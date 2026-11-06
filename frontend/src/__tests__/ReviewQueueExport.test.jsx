import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReviewQueue from '../pages/ReviewQueue';
import { exportReviewQueue, getReviewQueue } from '../services/reviewQueueService';
import { fetchProjects } from '../services/api';
import { ProjectProvider } from '../components/ProjectContext';
import { ToastProvider } from '../components/ToastContext';

vi.mock('../services/reviewQueueService', () => ({
  getReviewQueue: vi.fn(),
  exportReviewQueue: vi.fn(),
  resolveReviewItem: vi.fn(),
}));

vi.mock('../services/api', () => ({
  fetchProjects: vi.fn().mockResolvedValue([{ id: 1, name: 'Project Alpha' }]),
  default: {},
}));

describe('ReviewQueue Export', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('aqg_active_project_id', '1');
    fetchProjects.mockResolvedValue([{ id: 1, name: 'Project Alpha' }]);

    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    getReviewQueue.mockResolvedValue({
      data: [
        {
          id: 101,
          item_id: 101,
          external_id: 'EXT-101',
          content: { text: 'Item 1' },
          score: 0.42,
          flagged: true,
          resolution: null,
          annotations: [],
        },
      ],
      pagination: {
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderComponent = () =>
    render(
      <ToastProvider>
        <ProjectProvider>
          <ReviewQueue />
        </ProjectProvider>
      </ToastProvider>
    );

  it('triggers CSV download with temporary link element', async () => {
    const fakeBlob = new Blob(['item_id,label\n1,Pos'], { type: 'text/csv' });
    exportReviewQueue.mockResolvedValueOnce(fakeBlob);

    const createObjectURLMock = vi.fn().mockReturnValue('blob:http://localhost/test-uuid');
    const revokeObjectURLMock = vi.fn();
    window.URL.createObjectURL = createObjectURLMock;
    window.URL.revokeObjectURL = revokeObjectURLMock;

    renderComponent();

    expect(await screen.findByText('#101')).toBeInTheDocument();

    const exportBtn = screen.getByRole('button', { name: /Export Dataset/i });
    fireEvent.click(exportBtn);

    const downloadBtn = await screen.findByRole('button', { name: /Download CSV/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(exportReviewQueue).toHaveBeenCalledWith(1, 'csv');
      expect(createObjectURLMock).toHaveBeenCalled();
      expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:http://localhost/test-uuid');
    });
  });

  it('triggers JSON download with project ID', async () => {
    const fakeBlob = new Blob(['[{"item_id": 1}]'], { type: 'application/json' });
    exportReviewQueue.mockResolvedValueOnce(fakeBlob);

    const createObjectURLMock = vi.fn().mockReturnValue('blob:http://localhost/json-uuid');
    const revokeObjectURLMock = vi.fn();
    window.URL.createObjectURL = createObjectURLMock;
    window.URL.revokeObjectURL = revokeObjectURLMock;

    renderComponent();

    expect(await screen.findByText('#101')).toBeInTheDocument();

    const exportBtn = screen.getByRole('button', { name: /Export Dataset/i });
    fireEvent.click(exportBtn);

    const jsonCard = await screen.findByText('JSON');
    fireEvent.click(jsonCard.closest('button'));

    const downloadBtn = await screen.findByRole('button', { name: /Download JSON/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(exportReviewQueue).toHaveBeenCalledWith(1, 'json');
      expect(createObjectURLMock).toHaveBeenCalled();
      expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:http://localhost/json-uuid');
    });
  });

  it('handles export failure with error toast', async () => {
    exportReviewQueue.mockRejectedValueOnce({
      response: { data: { detail: 'Export generation failed on server' } },
    });

    renderComponent();

    expect(await screen.findByText('#101')).toBeInTheDocument();

    const exportBtn = screen.getByRole('button', { name: /Export Dataset/i });
    fireEvent.click(exportBtn);

    const downloadBtn = await screen.findByRole('button', { name: /Download CSV/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(screen.getByText('Export generation failed on server')).toBeInTheDocument();
    });
  });
});
