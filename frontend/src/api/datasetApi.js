import apiClient from "./apiClient";

export const uploadDataset = (file) => {
  const form = new FormData();
  form.append("file", file);
  return apiClient.post("/datasets/upload", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};

export const listDatasets = () => apiClient.get("/datasets").then((r) => r.data);
export const validateDataset = (datasetId) => apiClient.post(`/datasets/${datasetId}/validate`).then((r) => r.data);
export const processDataset = (datasetId) => apiClient.post(`/datasets/${datasetId}/process`).then((r) => r.data);
export const selectDatasetForTraining = (datasetId) =>
  apiClient.post(`/datasets/${datasetId}/select-for-training`).then((r) => r.data);
export const getTrainingSelection = () => apiClient.get("/datasets/training-selection").then((r) => r.data);
export const resetTrainingSelection = () => apiClient.post("/datasets/reset-training-selection").then((r) => r.data);
export const getActiveDatasetSummary = () => apiClient.get("/datasets/active-summary").then((r) => r.data);
