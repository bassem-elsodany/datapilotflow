// API Version constant - can be overridden by environment variable
export const API_VERSION = import.meta.env.API_VERSION || "v1";
export const API_PREFIX = `/api/${API_VERSION}`;

// API Configuration with environment variable support
export const API_CONFIG = {
  version: API_VERSION,
  prefix: API_PREFIX,
  baseUrl: import.meta.env.API_BASE_URL || 'http://api:8800',
} as const;
