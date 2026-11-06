import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { ProjectProvider, useProject } from '../components/ProjectContext';
import { fetchProjects } from '../services/api';

vi.mock('../services/api', () => ({
  fetchProjects: vi.fn(),
  default: {},
}));

function TestConsumer() {
  const { projectId, project, projects, setProjectId } = useProject();
  return (
    <div>
      <span data-testid="active-id">{projectId || 'none'}</span>
      <span data-testid="active-name">{project?.name || 'none'}</span>
      <span data-testid="project-count">{projects.length}</span>
      <button onClick={() => setProjectId(2)}>Switch to 2</button>
    </div>
  );
}

describe('ProjectContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes and switches projects while persisting to localStorage', async () => {
    fetchProjects.mockResolvedValueOnce([
      { id: 1, name: 'Project Alpha' },
      { id: 2, name: 'Project Beta' },
    ]);

    render(
      <ProjectProvider>
        <TestConsumer />
      </ProjectProvider>
    );

    // Initial load selects first project
    await waitFor(() => {
      expect(screen.getByTestId('active-id')).toHaveTextContent('1');
    });
    expect(screen.getByTestId('active-name')).toHaveTextContent('Project Alpha');
    expect(screen.getByTestId('project-count')).toHaveTextContent('2');

    // Switch project
    act(() => {
      screen.getByText('Switch to 2').click();
    });

    expect(screen.getByTestId('active-id')).toHaveTextContent('2');
    expect(screen.getByTestId('active-name')).toHaveTextContent('Project Beta');
    expect(localStorage.getItem('aqg_active_project_id')).toBe('2');
  });
});
