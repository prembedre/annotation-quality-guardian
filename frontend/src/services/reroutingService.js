import api from './api';

export async function fetchPendingReroutes(projectId) {
  const params = projectId ? { project_id: projectId } : {};
  const { data } = await api.get('/rerouting/pending', { params });
  return data;
}

export async function assignReroute(
  itemId,
  reassignedAnnotatorId,
  reason = ''
) {
  const payload = {
    reassigned_annotator_id: Number(reassignedAnnotatorId),
  };

  if (reason.trim()) {
    payload.reason = reason.trim();
  }

  const { data } = await api.post(`/rerouting/${itemId}/assign`, payload);
  return data;
}

export async function fetchAutomationRules(projectId) {
  const params = projectId ? { project_id: projectId } : {};
  const { data } = await api.get('/automation/rules', { params });
  return data;
}

export async function updateAutomationRule(ruleId, active, projectId) {
  const params = projectId ? { project_id: projectId } : {};
  const { data } = await api.put(`/automation/rules/${ruleId}`, { active }, { params });
  return data;
}
