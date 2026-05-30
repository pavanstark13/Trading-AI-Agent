import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios';

// Service base URLs (via nginx proxy in production, direct in dev)
const SERVICE_URLS = {
  marketData: import.meta.env.VITE_MARKET_DATA_URL || '/api/market-data',
  strategy: import.meta.env.VITE_STRATEGY_URL || '/api/strategy',
  risk: import.meta.env.VITE_RISK_URL || '/api/risk',
  execution: import.meta.env.VITE_EXECUTION_URL || '/api/execution',
  agent: import.meta.env.VITE_AGENT_URL || '/api/agent',
  monitoring: import.meta.env.VITE_MONITORING_URL || '/api/monitoring',
};

function createClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add auth token if available
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export const marketDataClient = createClient(`${SERVICE_URLS.marketData}/v1`);
export const strategyClient = createClient(`${SERVICE_URLS.strategy}/v1`);
export const riskClient = createClient(`${SERVICE_URLS.risk}/v1`);
export const executionClient = createClient(`${SERVICE_URLS.execution}/v1`);
export const agentClient = createClient(`${SERVICE_URLS.agent}/v1`);
export const monitoringClient = createClient(`${SERVICE_URLS.monitoring}/v1`);
