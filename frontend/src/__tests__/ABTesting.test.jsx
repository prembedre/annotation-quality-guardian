import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ABTesting from '../pages/ABTesting';
import api, { fetchProjects } from '../services/api';
import { ProjectProvider } from '../components/ProjectContext';
import { ToastProvider } from '../components/ToastContext';

vi.mock('../services/api', () => {
  const mockApi = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  };
  return {
    default: mockApi,
    fetchProjects: vi.fn(),
  };
});

describe('ABTesting Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('aqg_active_project_id', '1');
    fetchProjects.mockResolvedValue([{ id: 1, name: 'Project Alpha' }]);
  });

  const renderComponent = () =>
    render(
      <ToastProvider>
        <ProjectProvider>
          <ABTesting />
        </ProjectProvider>
      </ToastProvider>
    );

  it('renders empty state when no active experiments exist', async () => {
    api.get.mockResolvedValue({ data: { experiments: [] } });

    renderComponent();

    expect(await screen.findByText('No Active A/B Testing Experiment')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start New Guideline Test/i })).toBeInTheDocument();
  });

  it('opens modal and creates a new experiment', async () => {
    api.get.mockResolvedValueOnce({ data: { experiments: [] } });

    renderComponent();

    const startBtn = await screen.findByRole('button', { name: /Start New Guideline Test/i });
    fireEvent.click(startBtn);

    expect(screen.getByText('Start New Guideline A/B Test')).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText('e.g. Contrastive Edge-Case Guidelines v2');
    const descAInput = screen.getByPlaceholderText('Baseline production instructions');
    const descBInput = screen.getByPlaceholderText('Revised instructions with boundary contrast examples');

    fireEvent.change(nameInput, { target: { value: 'Guideline Clarity Trial' } });
    fireEvent.change(descAInput, { target: { value: 'Standard instructions' } });
    fireEvent.change(descBInput, { target: { value: 'Updated anchor examples' } });

    api.post.mockResolvedValueOnce({
      data: {
        id: 10,
        experiment_name: 'Guideline Clarity Trial',
        status: 'active',
      },
    });
    api.get.mockResolvedValueOnce({
      data: {
        experiments: [
          {
            id: 10,
            experiment_name: 'Guideline Clarity Trial',
            status: 'active',
            schema_version_a: { description: 'Standard instructions' },
            schema_version_b: { description: 'Updated anchor examples' },
            traffic_split_percent: 50,
          },
        ],
      },
    });
    api.get.mockResolvedValueOnce({
      data: {
        experiment_id: 10,
        variant_a: { total_annotations: 50, accuracy: 0.82, agreement_rate: 0.75, avg_duration_ms: 1200 },
        variant_b: { total_annotations: 50, accuracy: 0.94, agreement_rate: 0.88, avg_duration_ms: 950 },
        recommendation: 'Variant B demonstrates statistically significant accuracy improvement.',
      },
    });

    const createBtn = screen.getByRole('button', { name: /Launch Experiment/i });
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/ab-testing/experiments',
        expect.objectContaining({
          project_id: 1,
          experiment_name: 'Guideline Clarity Trial',
          schema_version_a: { description: 'Standard instructions' },
          schema_version_b: { description: 'Updated anchor examples' },
        })
      );
    });

    expect(await screen.findByText('Guideline Clarity Trial')).toBeInTheDocument();
  });

  it('promotes variant B when promote button is clicked', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/ab-testing/experiments') {
        return {
          data: {
            experiments: [
              {
                id: 10,
                experiment_name: 'Guideline Clarity Trial',
                status: 'active',
                schema_version_a: { description: 'Standard instructions' },
                schema_version_b: { description: 'Updated anchor examples' },
              },
            ],
          },
        };
      }
      return {
        data: {
          experiment_id: 10,
          variant_a: { total_annotations: 50, accuracy: 0.82, agreement_rate: 0.75, avg_duration_ms: 1200 },
          variant_b: { total_annotations: 50, accuracy: 0.94, agreement_rate: 0.88, avg_duration_ms: 950 },
          recommendation: 'Variant B demonstrates statistically significant accuracy improvement.',
        },
      };
    });

    api.post.mockResolvedValueOnce({
      data: {
        message: 'Variant B promoted to production guidelines!',
        winner: 'variant_b',
      },
    });

    renderComponent();

    expect(await screen.findByText('Guideline Clarity Trial')).toBeInTheDocument();

    const promoteBtn = screen.getByRole('button', { name: /Promote Variant B/i });
    fireEvent.click(promoteBtn);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/ab-testing/experiments/10/promote?variant=B'
      );
    });

    expect(
      await screen.findByText(/Variant B successfully promoted to production/i)
    ).toBeInTheDocument();
  });
});
