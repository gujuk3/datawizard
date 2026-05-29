import client from './client';

export const listModels = () =>
  client.get('/ml/').then((r) => r.data);

export const getModel = (id) =>
  client.get(`/ml/${id}/`).then((r) => r.data);

export const deleteModel = (id) =>
  client.delete(`/ml/${id}/delete/`).then((r) => r.data);

export const predict = (id, features) =>
  client.post(`/ml/${id}/predict/`, { features }).then((r) => r.data);

export const trainModel = (config) =>
  client.post('/ml/train/', config).then((r) => r.data);
