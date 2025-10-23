import axios from 'axios';
import { app } from '@/config';

export const client = axios.create({
  baseURL: app.apiBaseUrl,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-type': 'application/json',
    Accept: 'application/json',
  },
});

// Add request interceptor for debugging
client.interceptors.request.use(
  (config) => {
    // Check if this is an authentication endpoint that doesn't need a token
    const isAuthEndpoint = config.url?.includes('/auth/login') || config.url?.includes('/auth/register');
    
    if (!isAuthEndpoint) {
      // Check if we have a valid token before making any request
      const token = localStorage.getItem('jwt_token');
      if (!token || !token.trim()) {
        console.warn('🚫 Blocking API request: No authentication token available');
        // Create a rejected promise that will be thrown
        const error = new Error('No authentication token available');
        error.name = 'AuthenticationError';
        return Promise.reject(error);
      }
      
      // Ensure Authorization header is set
      if (!config.headers.authorization) {
        config.headers.authorization = `Bearer ${token}`;
      }
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
client.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.config?.url);
    console.error('❌ Error Details:', error.response?.data);
    return Promise.reject(error);
  }
);

export function setClientAccessToken(token: string) {
  if (token && token.trim()) {
    localStorage.setItem(app.accessTokenStoreKey, token);
    client.defaults.headers.common.authorization = `Bearer ${token}`;
  } else {
    removeClientAccessToken();
  }
}

export function removeClientAccessToken() {
  localStorage.removeItem(app.accessTokenStoreKey);
  delete client.defaults.headers.common.authorization;
}

export function loadAccessToken(): string | null {
  const token = localStorage.getItem(app.accessTokenStoreKey);
  if (token && token.trim()) {
    client.defaults.headers.common.authorization = `Bearer ${token}`;
    return token;
  }
  return null;
}

export function getStoredToken(): string | null {
  const token = localStorage.getItem(app.accessTokenStoreKey);
  return token && token.trim() ? token : null;
}
