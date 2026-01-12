// API Version constant - can be overridden by environment variable
export const API_VERSION = import.meta.env.VITE_API_VERSION || "v1";
export const API_PREFIX = `/api/${API_VERSION}`;

// API Configuration with environment variable support
export const API_CONFIG = {
  version: API_VERSION,
  prefix: API_PREFIX,
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:65500',
} as const;
