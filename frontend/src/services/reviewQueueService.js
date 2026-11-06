import api from './api';

/**
 * Fetch review queue data from backend API
 */
export async function getReviewQueue(params = {}) {
  const queryParams = {
    page: params.page || 1,
    page_size: params.pageSize || 10,
    project_id: params.projectId || 1, // Default to 1 if not provided
  };

  if (params.status && params.status !== 'all') {
    queryParams.flagged = params.status === 'flagged';
  }

  if (params.search) {
    queryParams.search = params.search;
  }

  if (params.riskFilter && params.riskFilter !== 'all') {
    if (params.riskFilter === 'high') {
      queryParams.min_score = 0.85;
    } else if (params.riskFilter === 'medium') {
      queryParams.min_score = 0.70;
      queryParams.max_score = 0.8499;
    } else if (params.riskFilter === 'low') {
      queryParams.max_score = 0.6999;
    }
  }

  const { data } = await api.get('/review/queue', { params: queryParams });
  return {
    data: data.items,
    pagination: {
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
      totalPages: data.total_pages,
    },
  };
}

/**
 * Export review queue in the specified format from backend API
 */
export async function exportReviewQueue(projectId, format = 'csv') {
  // Gracefully handle reversed args if any caller passes (format, { projectId, ... })
  let effectiveProjectId = projectId;
  let effectiveFormat = format;

  if (typeof projectId === 'string' && (projectId === 'csv' || projectId === 'json') && typeof format === 'object') {
    effectiveFormat = projectId;
    effectiveProjectId = format?.projectId || 1;
  }

  const response = await api.get(`/projects/${effectiveProjectId}/export`, {
    params: { format: effectiveFormat },
    responseType: 'blob',
  });
  
  return response.data;
}

/**
 * Resolve a review item
 */
export async function resolveReviewItem(itemId, payload) {
  const { data } = await api.post(`/review/${itemId}/resolve`, payload);
  return data;
}
