import apiClient from "./apiClient";

export const listAssessments = (athleteId) =>
  apiClient.get(`/athletes/${athleteId}/assessments`).then((r) => r.data);

export const createAssessment = (athleteId, payload) =>
  apiClient.post(`/athletes/${athleteId}/assessments`, payload).then((r) => r.data);

export const getAssessment = (assessmentId) =>
  apiClient.get(`/assessments/${assessmentId}`).then((r) => r.data);
