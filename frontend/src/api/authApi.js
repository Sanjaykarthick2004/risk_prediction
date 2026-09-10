import apiClient from "./apiClient";

export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await apiClient.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function register(username, password, role = "RESEARCHER") {
  const res = await apiClient.post("/auth/register", { username, password, role });
  return res.data;
}

export async function getMe() {
  const res = await apiClient.get("/auth/me");
  return res.data;
}

export async function forgotPassword(username) {
  const res = await apiClient.post("/auth/forgot-password", { username });
  return res.data;
}

export async function resetPassword(token, newPassword) {
  const res = await apiClient.post("/auth/reset-password", { token, new_password: newPassword });
  return res.data;
}
