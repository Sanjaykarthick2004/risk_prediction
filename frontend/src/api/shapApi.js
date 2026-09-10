import apiClient from "./apiClient";

export const getGlobalExplanation = () => apiClient.get("/explainability/global").then((r) => r.data);

export const getPredictionExplanation = (predictionId) =>
  apiClient.get(`/explainability/${predictionId}`).then((r) => r.data);

export const getWaterfall = (predictionId) =>
  apiClient.get(`/explainability/${predictionId}/waterfall`).then((r) => r.data);

export const getDependence = (feature) =>
  apiClient.get(`/explainability/dependence/${feature}`).then((r) => r.data);
