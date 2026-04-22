/**
 * SecureWealth Twin — Axios API Client
 */

import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach token ─────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: surface error messages ──────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail;
    const message = typeof detail === 'object' 
      ? JSON.stringify(detail)
      : (detail || error?.response?.data?.message || error?.message || 'An unexpected error occurred');
    
    return Promise.reject(new Error(message));
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  login:    (email, password) =>
    apiClient.post('/api/v1/auth/login',    { email, password }),
  register: (email, password, full_name) =>
    apiClient.post('/api/v1/auth/register', { email, password, full_name }),
  me:       () => apiClient.get('/api/v1/auth/me'),
};

// ── Net Worth ─────────────────────────────────────────────────────────────────
export const networthAPI = {
  get:       () => apiClient.get('/api/v1/networth'),
  recompute: () => apiClient.post('/api/v1/networth/recompute'),
  history:   (limit = 12) => apiClient.get(`/api/v1/networth/history?limit=${limit}`),
};

// ── Account Aggregator ────────────────────────────────────────────────────────
export const aggregatorAPI = {
  accounts:        () => apiClient.get('/api/v1/aggregator/accounts'),
  financialPicture:() => apiClient.get('/api/v1/aggregator/financial-picture'),
  consents:        () => apiClient.get('/api/v1/aggregator/consents'),
  createConsent:   (payload) => apiClient.post('/api/v1/aggregator/consents', payload),
  fetch:           (consent_id) => apiClient.post('/api/v1/aggregator/fetch', { consent_id }),
};

// ── Physical Assets ───────────────────────────────────────────────────────────
export const assetsAPI = {
  list:    (category) =>
    apiClient.get(category ? `/api/v1/assets?category=${category}` : '/api/v1/assets'),
  summary: () => apiClient.get('/api/v1/assets/summary'),
  create:  (data, securityToken = null) => 
    apiClient.post(securityToken ? `/api/v1/assets?security_token=${securityToken}` : '/api/v1/assets', data),
  update:  (id, data) => apiClient.patch(`/api/v1/assets/${id}`, data),
  delete:  (id) => apiClient.delete(`/api/v1/assets/${id}`),
};

// ── Wealth Advisor ────────────────────────────────────────────────────────────
export const advisorAPI = {
  getRecommendations: () => apiClient.get('/api/v1/advisor/recommendations'),
};

// ── Scenario Simulator ────────────────────────────────────────────────────────
export const simulatorAPI = {
  run: (payload) => apiClient.post('/api/v1/simulator/run', payload),
};

// ── AI Chat Advisor ───────────────────────────────────────────────────────────
export const chatAPI = {
  ask: (message) => apiClient.post('/api/v1/chat/ask', { message }),
};

// ── Blockchain Audit ──────────────────────────────────────────────────────────
export const auditAPI = {
  getTrail: (limit = 10) => apiClient.get(`/api/v1/audit?limit=${limit}`),
};

export default apiClient;
