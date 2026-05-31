import axios, { type AxiosInstance } from 'axios';

// All services consolidated into ai-agent — single base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1';

function createClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
      }
      return Promise.reject(error);
    },
  );

  return client;
}

// Single client — all endpoints live on the ai-agent service
export const agentClient = createClient(API_BASE);
export const marketDataClient = agentClient;
export const strategyClient = agentClient;
export const riskClient = agentClient;
export const executionClient = agentClient;
export const monitoringClient = agentClient;
