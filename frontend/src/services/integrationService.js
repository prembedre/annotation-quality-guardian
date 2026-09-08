import api from './api';

export async function fetchConnectors(status) {
  const params = {};

  if (status) {
    params.status = status;
  }

  const { data } = await api.get('/integrations/connectors', {
    params,
  });

  return data;
}

export async function createConnector(payload) {
  const { data } = await api.post(
    '/integrations/connectors',
    payload
  );

  return data;
}

export async function testConnector(connectorId) {
  const { data } = await api.post(
    `/integrations/connectors/${connectorId}/test`
  );

  return data;
}

export async function deleteConnector(connectorId) {
  const { data } = await api.delete(
    `/integrations/connectors/${connectorId}`
  );

  return data;
}

export async function syncConnector(connectorId, payload) {
  const { data } = await api.post(
    `/integrations/connectors/${connectorId}/sync`,
    payload
  );

  return data;
}