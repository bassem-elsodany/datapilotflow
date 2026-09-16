// Injected into window at container startup — see
// docker/services/dashboard/docker-entrypoint.sh. Takes precedence over the
// build-time VITE_API_BASE_URL so a single published image works whether
// it's reached at localhost or a remote host, without rebuilding.
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: { API_BASE_URL?: string };
  }
}

// API Version constant - can be overridden by environment variable
export const API_VERSION = import.meta.env.VITE_API_VERSION || "v1";
export const API_PREFIX = `/api/${API_VERSION}`;

// API Configuration with environment variable support
export const API_CONFIG = {
  version: API_VERSION,
  prefix: API_PREFIX,
  baseUrl:
    window.__RUNTIME_CONFIG__?.API_BASE_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    'http://localhost:65500',
} as const;
