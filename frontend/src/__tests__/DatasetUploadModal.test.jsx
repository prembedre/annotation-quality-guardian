import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DatasetUploadModal } from '../components/DatasetUploadModal';
import { uploadDataset } from '../services/api';

vi.mock('../services/api', () => ({
  uploadDataset: vi.fn(),
  fetchProjects: vi.fn(),
  default: {},
}));

describe('DatasetUploadModal', () => {
  const projects = [
    { id: 1, name: 'Project Alpha' },
    { id: 2, name: 'Project Beta' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('rejects unsupported file extensions with an error message', async () => {
    render(
      <DatasetUploadModal
        isOpen={true}
        onClose={vi.fn()}
        projects={projects}
        activeProjectId={1}
      />
    );

    const input = document.querySelector('input[type="file"]');
    const invalidFile = new File(['hello'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(await screen.findByText(/Unsupported file type/i)).toBeInTheDocument();
  });

  it('uploads valid CSV and displays ingestion metrics on success', async () => {
    uploadDataset.mockResolvedValueOnce({
      total_records: 44,
      inserted_records: 42,
      duplicate_records: 2,
      failed_records: 0,
      filename: 'sample.csv',
    });

    const onSuccess = vi.fn();

    render(
      <DatasetUploadModal
        isOpen={true}
        onClose={vi.fn()}
        projects={projects}
        activeProjectId={1}
        onSuccess={onSuccess}
      />
    );

    const input = document.querySelector('input[type="file"]');
    const validFile = new File(['item_id,label\n1,Positive'], 'sample.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [validFile] } });

    // File selected display
    expect(screen.getByText('sample.csv')).toBeInTheDocument();

    // Click upload
    const uploadBtn = screen.getByRole('button', { name: /Upload & Ingest/i });
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(uploadDataset).toHaveBeenCalledWith(validFile, 1, expect.any(Function));
    });

    expect(await screen.findByText('Ingestion Complete')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(onSuccess).toHaveBeenCalled();
  });

  it('displays error message when backend upload fails', async () => {
    uploadDataset.mockRejectedValueOnce({
      response: { data: { detail: 'Missing required item_id column in CSV' } },
    });

    render(
      <DatasetUploadModal
        isOpen={true}
        onClose={vi.fn()}
        projects={projects}
        activeProjectId={1}
      />
    );

    const input = document.querySelector('input[type="file"]');
    const validFile = new File(['bad_content'], 'invalid.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [validFile] } });
    fireEvent.click(screen.getByRole('button', { name: /Upload & Ingest/i }));

    expect(await screen.findByText(/Missing required item_id column in CSV/i)).toBeInTheDocument();
  });
});
