// frontend/src/services/api.js
//
// Single Axios instance. Every API call goes through here.
// Benefits: one place to add auth headers, handle 401s, base URL.
// NEVER call fetch/axios directly in components — always use this file.
//
import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://127.0.0.1:8000",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach JWT to every request automatically ──────────
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("sars_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle expired tokens globally ───────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear session and redirect to login
      sessionStorage.clear();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth endpoints ──────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login:    (data) => api.post("/auth/login", data),
  me:       ()     => api.get("/auth/me"),
};

// ── Student endpoints (populated further in Goals 2-4) ─────────────────────
export const studentAPI = {
  getProfile: () => api.get("/student/profile"),
};

// ── Teacher endpoints (populated further in Goal 5) ────────────────────────
export const teacherAPI = {
  getProfile:  () => api.get("/teacher/profile"),
  getStudents: () => api.get("/teacher/students"),
};

export default api;
