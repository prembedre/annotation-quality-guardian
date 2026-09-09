import api from './api';

export async function fetchPendingReroutes() {
  const { data } = await api.get('/rerouting/pending');
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