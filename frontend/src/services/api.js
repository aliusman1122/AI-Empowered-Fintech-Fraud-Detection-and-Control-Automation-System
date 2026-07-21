import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 1. JWT Request Interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("finguard_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => Promise.reject(error));

// 2. JWT Response Interceptor (401 Redirect Wrapper)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem("finguard_token");
            localStorage.removeItem("finguard_user");
            // Hard redirect bypassing router bounds to ensure state purge
            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// ── Auth Endpoints ──────────────────────────────────────────────
export const loginUser = async (credentials) => {
    // FastAPI expects application/x-www-form-urlencoded format for OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', credentials.username); // 'username' holds the 'email'
    formData.append('password', credentials.password);

    const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
};

export const registerUser = async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
};

export const getSystemStats = async () => {
    try {
        const response = await api.get('/stats');
        return response.data;
    } catch (error) {
        console.error('Failed to fetch stats:', error);
        throw error;
    }
};

export const getTransactions = async (limit = 50) => {
    try {
        const response = await api.get(`/transactions/?limit=${limit}`);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch transactions:', error);
        throw error;
    }
};

export const predictTransaction = async (transactionData) => {
    try {
        const response = await api.post('/transactions/predict', transactionData);
        return response.data;
    } catch (error) {
        console.error('Failed to predict transaction:', error);
        throw error;
    }
};

export const subscribeToTransactions = (onMessage) => {
    const token = localStorage.getItem("finguard_token");
    if (!token) return null; // Safe guard

    const eventSource = new EventSource(`${API_BASE_URL}/transactions/stream?token=${token}`);

    eventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            if (!data.error) {
                onMessage(data);
            }
        } catch (err) {
            console.warn("Error parsing SSE data", err);
        }
    };

    eventSource.onerror = (err) => {
        console.warn('SSE connection error. Closing stream to prevent browser lockup loop.', err);
        eventSource.close();
    };

    return eventSource;
};
