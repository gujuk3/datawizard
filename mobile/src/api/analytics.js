import client from './client';

export const getStatistics = (datasetId) =>
  client.get(`/analytics/${datasetId}/statistics/`).then((r) => r.data);

export const getCorrelation = (datasetId) =>
  client.get(`/analytics/${datasetId}/correlation/`).then((r) => r.data);

export const getMissingValues = (datasetId) =>
  client.get(`/analytics/${datasetId}/missing/`).then((r) => r.data);

export const getLLMExplain = (datasetId) =>
  client.post(`/analytics/${datasetId}/explain/`, {}).then((r) => r.data);

export const preprocess = (datasetId, config) =>
  client.post(`/analytics/${datasetId}/preprocess/`, config).then((r) => r.data);
