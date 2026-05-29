import client from './client';

export const listDatasets = () =>
  client.get('/datasets/').then((r) => r.data);

export const getDataset = (id) =>
  client.get(`/datasets/${id}/`).then((r) => r.data);

export const previewDataset = (id) =>
  client.get(`/datasets/${id}/preview/`).then((r) => r.data);

export const deleteDataset = (id) =>
  client.delete(`/datasets/${id}/delete/`).then((r) => r.data);

export async function uploadDataset(fileUri, fileName, mimeType = 'text/csv') {
  const form = new FormData();
  form.append('file', { uri: fileUri, name: fileName, type: mimeType });
  const { data } = await client.post('/datasets/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
