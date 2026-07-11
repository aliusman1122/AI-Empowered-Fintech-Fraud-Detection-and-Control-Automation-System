import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
