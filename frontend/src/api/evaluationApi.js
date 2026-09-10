import apiClient from "./apiClient";

export const getModelComparison = () => apiClient.get("/evaluation/models").then((r) => r.data);
export const getMetrics = () => apiClient.get("/evaluation/metrics").then((r) => r.data);
export const getConfusionMatrix = () => apiClient.get("/evaluation/confusion-matrix").then((r) => r.data);
export const getRocCurve = () => apiClient.get("/evaluation/roc-curve").then((r) => r.data);
export const getPrecisionRecall = () => apiClient.get("/evaluation/precision-recall").then((r) => r.data);
export const getModalityAblation = () => apiClient.get("/evaluation/modality-ablation").then((r) => r.data);

export const trainBaselines = () => apiClient.post("/training/train").then((r) => r.data);
export const trainXgboostDefault = () => apiClient.post("/training/xgboost").then((r) => r.data);
export const optimizeXgboost = (nIter = 30) =>
  apiClient.post("/training/optimize", null, { params: { n_iter: nIter } }).then((r) => r.data);
export const runAblation = () => apiClient.post("/training/ablation").then((r) => r.data);
export const getTrainingStatus = () => apiClient.get("/training/status").then((r) => r.data);
export const autoSelectBestDataset = (nIter = 30) =>
  apiClient.post("/training/auto-select-best-dataset", null, { params: { n_iter: nIter } }).then((r) => r.data);
