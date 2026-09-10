import apiClient from "./apiClient";

export const createPrediction = (payload) => apiClient.post("/predictions", payload).then((r) => r.data);

export const listPredictions = (athleteId) =>
  apiClient.get("/predictions", { params: athleteId ? { athlete_id: athleteId } : {} }).then((r) => r.data);

export const getPrediction = (predictionId) =>
  apiClient.get(`/predictions/${predictionId}`).then((r) => r.data);

export const getAthletePredictions = (athleteId) =>
  apiClient.get(`/athletes/${athleteId}/predictions`).then((r) => r.data);
