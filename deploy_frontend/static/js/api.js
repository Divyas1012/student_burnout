/**
 * api.js
 * Centralized REST API client for communicating with FastAPI backend.
 */

const API_BASE = window.MIND_PULSE_API_URL || localStorage.getItem("MIND_PULSE_API_URL") || "";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const API = {
  // Auth & Profiles
  login: (email, password) => request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }),
  register: (userData) => request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(userData),
  }),
  getUsers: () => request("/api/auth/users"),
  getUserProfile: (userId) => request(`/api/auth/current-user/${userId}`),

  // Surveys & Predictions
  submitSurvey: (studentId, data) => request(`/api/surveys/submit/${studentId}`, {
    method: "POST",
    body: JSON.stringify(data),
  }),
  getSurveyHistory: (studentId) => request(`/api/surveys/history/${studentId}`),
  evaluateRiskPreview: (data) => request("/api/predict/evaluate", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  getModelInfo: () => request("/api/predict/model-info"),

  // Counselor & Admin
  getCohortSummary: () => request("/api/analytics/cohort-summary"),
  getAlerts: (status = "ALL") => request(`/api/counselor/alerts?status=${encodeURIComponent(status)}`),
  updateAlertStatus: (alertId, data) => request(`/api/counselor/alerts/${alertId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  }),
  getStudentsRoster: (riskFilter = "ALL", search = "") => 
    request(`/api/counselor/students?risk_filter=${encodeURIComponent(riskFilter)}&search=${encodeURIComponent(search)}`),
  getStudentDetail: (studentId) => request(`/api/counselor/students/${studentId}`),
};
