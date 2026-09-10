import apiClient from "./apiClient";

export const getPredictionReport = (predictionId) =>
  apiClient.get(`/reports/prediction/${predictionId}`).then((r) => r.data);

export const getAthleteReport = (athleteId) =>
  apiClient.get(`/reports/athlete/${athleteId}`).then((r) => r.data);
