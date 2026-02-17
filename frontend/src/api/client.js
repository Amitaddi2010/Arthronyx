import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 120000, // 120s — pipeline: 3 API fetches + rerank + LLM synthesis
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('arthronyx_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export const api = {
    checkHealth: () => apiClient.get('/health'),

    queryEvidence: (payload) => apiClient.post('/query', payload),

    getAuditLogs: (skip = 0, limit = 20) =>
        apiClient.get('/audit', { params: { skip, limit } }),

    getCitationGraph: (doi) => apiClient.get(`/citations/${encodeURIComponent(doi)}`),

    triggerIngestion: (params) => apiClient.post('/ingest', null, { params }),
};
