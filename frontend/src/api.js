import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api'
});

// Add auth token to requests
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (data) => API.post('/auth/register', data);
export const login = (data) => API.post('/auth/login', data);
export const passkeyRegisterStart = (data) => API.post('/auth/passkey/register/start', data);
export const passkeyRegisterVerify = (data) => API.post('/auth/passkey/register/verify', data);
export const passkeyAuthStart = (data) => API.post('/auth/passkey/auth/start', data);
export const passkeyAuthVerify = (data) => API.post('/auth/passkey/auth/verify', data);

// Contacts
export const getContacts = (params) => API.get('/contacts/', { params });
export const getContact = (id) => API.get(`/contacts/${id}`);
export const createContact = (data) => API.post('/contacts/', data);
export const updateContact = (id, data) => API.put(`/contacts/${id}`, data);
export const deleteContact = (id) => API.delete(`/contacts/${id}`);
export const getContactInteractions = (id) => API.get(`/contacts/${id}/interactions`);
export const createInteraction = (id, data) => API.post(`/contacts/${id}/interactions`, data);
export const importContacts = (formData) => API.post('/contacts/import', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

// Deals
export const getDeals = (params) => API.get('/deals/', { params });
export const createDeal = (data) => API.post('/deals/', data);
export const updateDeal = (id, data) => API.put(`/deals/${id}`, data);
export const deleteDeal = (id) => API.delete(`/deals/${id}`);

// Tasks
export const getTasks = (params) => API.get('/tasks/', { params });
export const createTask = (data) => API.post('/tasks/', data);
export const updateTask = (id, data) => API.put(`/tasks/${id}`, data);
export const deleteTask = (id) => API.delete(`/tasks/${id}`);

// Dashboard
export const getMetrics = () => API.get('/dashboard/metrics');
export const getPipeline = () => API.get('/dashboard/pipeline');

// Agents
export const getProspecting = () => API.get('/agents/prospecting');
export const getNurturing = () => API.get('/agents/nurturing');
export const runHealthScores = () => API.post('/agents/health-score');

// NLI
export const nlQuery = (query) => API.post('/nli/query', { query });

// Creator Studio
export const getPersonas = () => API.get('/creator/personas');
export const getPersonaPortfolio = (id) => API.get(`/creator/personas/${id}/portfolio`);
export const getQueue = () => API.get('/creator/queue');
export const approveAssets = (assetIds) => API.post('/creator/queue/approve', { asset_ids: assetIds });
export const rejectAssets = (assetIds, reason) => API.post('/creator/queue/reject', { asset_ids: assetIds, reason });
export const getMetricsSummary = (personaId, days = 30) => API.get('/creator/metrics/summary', { params: { persona_id: personaId, days } });
export const getFlaggedMetrics = () => API.get('/creator/metrics/flagged');
export const runBatch = () => API.post('/creator/batch/run');
export const getGraduation = (id) => API.get(`/creator/personas/${id}/graduation`);
export const getInstagramAccounts = () => API.get('/creator/instagram-accounts');

export default API;
