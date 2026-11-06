import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AutomationDashboard from '../pages/AutomationDashboard';
import * as reroutingService from '../services/reroutingService';
import { fetchProjects } from '../services/api';
import { ProjectProvider } from '../components/ProjectContext';
import { ToastProvider } from '../components/ToastContext';

vi.mock('../services/api', () => ({
  default: {},
  fetchProjects: vi.fn(),
}));

vi.mock('../services/reroutingService', () => ({
  fetchPendingReroutes: vi.fn(),
  assignReroute: vi.fn(),
  fetchAutomationRules: vi.fn(),
  updateAutomationRule: vi.fn(),
}));

describe('AutomationDashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('aqg_active_project_id', '1');
    fetchProjects.mockResolvedValue([{ id: 1, name: 'Project Alpha' }]);

    reroutingService.fetchAutomationRules.mockResolvedValue([
      {
        id: 'rule-1',
        title: 'Low Trust Score Escalation',
        condition: 'Annotator Trust Score < 60% AND Confidence < 70%',
        action: 'Reassign automatically to Senior Tier (Annotator #3)',
        active: true,
      },
      {
        id: 'rule-2',
        title: 'Taxonomy Ambiguity Consensus',
        condition: 'Class Disagreement Rate > 20% on Ambiguous Classes',
        action: 'Require 2x Overlapping Annotator Verification',
        active: true,
      },
      {
        id: 'rule-3',
        title: 'Latent Space Outlier Quarantine',
        condition: 'Embedding Cosine Distance > 0.80 from Centroid',
        action: 'Route directly to Expert Review Queue',
        active: false,
      },
    ]);

    reroutingService.fetchPendingReroutes.mockResolvedValue({
      total: 1,
      items: [
        {
          item_id: 42,
          content: 'Ambiguous text sentence for testing',
          original_annotator_id: 2,
          original_annotator_name: 'Annotator #2',
          reason: 'Trust score < 60%',
          created_at: new Date().toISOString(),
        },
      ],
    });
  });

  const renderComponent = () =>
    render(
      <ToastProvider>
        <ProjectProvider>
          <AutomationDashboard />
        </ProjectProvider>
      </ToastProvider>
    );

  it('loads and renders automation rules and pending reroutes', async () => {
    renderComponent();

    expect(await screen.findByText('Low Trust Score Escalation')).toBeInTheDocument();
    expect(screen.getByText('Taxonomy Ambiguity Consensus')).toBeInTheDocument();
    expect(screen.getByText('Latent Space Outlier Quarantine')).toBeInTheDocument();

    expect(await screen.findByText('#42')).toBeInTheDocument();
    expect(screen.getByText('Ambiguous text sentence for testing')).toBeInTheDocument();
  });

  it('toggles rule status and calls updateAutomationRule', async () => {
    reroutingService.updateAutomationRule.mockResolvedValue({ success: true });

    renderComponent();

    // The third rule is PAUSED initially
    const pausedButton = await screen.findByRole('button', { name: 'PAUSED' });
    fireEvent.click(pausedButton);

    await waitFor(() => {
      expect(reroutingService.updateAutomationRule).toHaveBeenCalledWith('rule-3', true, 1);
    });

    expect(
      await screen.findByText('Automation policy "Latent Space Outlier Quarantine" updated.')
    ).toBeInTheDocument();
  });

  it('opens reassignment modal and assigns task to target annotator', async () => {
    reroutingService.assignReroute.mockResolvedValue({
      message: 'Item #42 successfully reassigned to Annotator #3!',
    });

    renderComponent();

    expect(await screen.findByText('#42')).toBeInTheDocument();

    const reassignBtn = screen.getByRole('button', { name: /Reassign/i });
    fireEvent.click(reassignBtn);

    expect(screen.getByText('Reassign Task to Qualified Annotator')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/e\.g\. 1 \(Prem\)/i);
    fireEvent.change(input, { target: { value: '3' } });

    const confirmBtn = screen.getByRole('button', { name: /Confirm Assignment/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(reroutingService.assignReroute).toHaveBeenCalledWith(
        42,
        '3',
        'Automated policy reassignment'
      );
    });

    expect(
      await screen.findByText('Item #42 successfully reassigned to Annotator #3!')
    ).toBeInTheDocument();
  });
});
