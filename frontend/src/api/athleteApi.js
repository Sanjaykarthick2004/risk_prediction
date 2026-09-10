import apiClient from "./apiClient";

export const listAthletes = (search = "") =>
  apiClient.get("/athletes", { params: search ? { search } : {} }).then((r) => r.data);

export const createAthlete = (payload) => apiClient.post("/athletes", payload).then((r) => r.data);

export const getAthlete = (athleteId) => apiClient.get(`/athletes/${athleteId}`).then((r) => r.data);

export const updateAthlete = (athleteId, payload) =>
  apiClient.put(`/athletes/${athleteId}`, payload).then((r) => r.data);

export const deleteAthlete = (athleteId) => apiClient.delete(`/athletes/${athleteId}`);
