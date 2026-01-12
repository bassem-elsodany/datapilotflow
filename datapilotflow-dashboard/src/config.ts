import { API_CONFIG } from './constants';

// Environment detection
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;

// Get current environment
const getCurrentEnvironment = () => {
  if (import.meta.env.ENVIRONMENT === 'production') return 'production';
  if (import.meta.env.ENVIRONMENT === 'staging') return 'staging';
  return 'development';
};

const currentEnv = getCurrentEnvironment();

// Build API base URL
const buildApiBaseUrl = () => {
  const baseUrl = API_CONFIG.baseUrl.replace(/\/$/, ''); // Remove trailing slash
  return `${baseUrl}${API_CONFIG.prefix}`;
};

// Centralized API Endpoints Configuration
export const apiEndpoints = {
  // Authentication
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    passwordReset: '/auth/password/reset',
    passwordResetConfirm: '/auth/password/reset/confirm',
    refresh: '/auth/refresh',
  },

  // User Management
  users: {
    me: '/users/me',
    profile: '/users/me',
    changePassword: '/users/me/change-password',
    deleteAccount: '/users/me',
    list: '/users',
    create: '/users',
    user: (userId: string) => `/users/${userId}`,
  },

  // User Roles Management
  roles: {
    list: '/roles',
    create: '/roles',
    role: (roleId: string) => `/roles/${roleId}`,
    permissions: '/roles/permissions',
    assign: '/roles/assign',
    remove: '/roles/remove',
    userRoles: (userId: string) => `/roles/user/${userId}`,
  },

  // Conversations
  conversations: {
    chat: '/conversations',
    memory: '/conversations/memory',
    sessions: '/conversations',
    session: (sessionId: string) => `/conversations/${sessionId}`,
    sessionName: (sessionId: string) => `/conversations/${sessionId}/name`,
    createSession: '/conversations/sessions',
    websocket: {
      // Real-time conversation chat with knowledge search
      search: (conversationId: string) => `/ws/conversations/${conversationId}/search`,
    },
  },

  // Agent (LangGraph Workflow)
  agent: {
    websocket: {
      // RAG-only mode - direct retrieval without intent detection or task routing
      rag: '/ws/agent/query/rag',
      // Multi-agent supervisor mode with intent routing (RAG + optional Task execution)
      supervisor: '/ws/agent/query/supervisor',
      // Legacy mixed-mode endpoint (deprecated - use rag or supervisor instead)
      query: '/ws/agent/query',
    },
  },

  // Knowledge Source Configuration (RAG Settings)
  knowledgeSources: {
    // Configuration Management
    configs: '/knowledge/sources',
    config: (configId: string) => `/knowledge/sources/${configId}`,

    // URL Source Management (nested under config - RESTful)
    urlSource: (configId: string, urlSourceId: string) => `/knowledge/sources/${configId}/url-sources/${urlSourceId}`,

    // Job Management (moved to separate endpoint)
    configJobs: (configId: string) => `/knowledge/sources/${configId}/jobs`,
  },

  // Knowledge Job Management (separate endpoint)
  knowledgeJobs: {
    list: '/knowledge/jobs',
    create: (configId: string) => `/knowledge/sources/${configId}/jobs`,
    job: (jobId: string) => `/knowledge/jobs/${jobId}`,
    update: (jobId: string) => `/knowledge/jobs/${jobId}`,
    delete: (jobId: string) => `/knowledge/jobs/${jobId}`,
    execute: (jobId: string) => `/knowledge/jobs/${jobId}/execute`,
    cancel: (jobId: string) => `/knowledge/jobs/${jobId}/cancel`,
  },

  // Job Timeline Management
  jobTimelines: {
    listByJob: (jobId: string) => `/knowledge/jobs/${jobId}/timelines`,
    get: (timelineId: string) => `/knowledge/jobs/timelines/${timelineId}`,
    getLatest: (jobId: string) => `/knowledge/jobs/${jobId}/timelines?latest=true`,
    getStatistics: (jobId: string) => `/knowledge/jobs/${jobId}/timelines/statistics`,
    update: (timelineId: string) => `/knowledge/jobs/timelines/${timelineId}`,
  },

  // Vector DB Collection Management
  vectordb: {
    // Milvus collection endpoints (for vector-status page)
    collections: '/vectordb/collections',
    collection: (collectionId: string) => `/vectordb/collections/${collectionId}`,
    schema: (collectionId: string) => `/vectordb/collections/${collectionId}/schema`,
    stats: (collectionId: string) => `/vectordb/collections/${collectionId}/stats`,
    records: (collectionId: string) => `/vectordb/collections/${collectionId}/records`,

    // Knowledge VectorDB collection configuration endpoints (for job view modal)
    knowledgeCollections: '/knowledge/vectordb-collections',
    knowledgeCollection: (collectionId: string) => `/knowledge/vectordb-collections/${collectionId}`,
    checkName: (name: string) => `/knowledge/vectordb-collections?name=${encodeURIComponent(name)}`,
  },

  // LLM Content Filter Management
  contentFilters: {
    list: '/knowledge/content-filters',
    create: '/knowledge/content-filters',
    filter: (filterId: string) => `/knowledge/content-filters/${filterId}`,
    update: (filterId: string) => `/knowledge/content-filters/${filterId}`,
    delete: (filterId: string) => `/knowledge/content-filters/${filterId}`,
    validate: (filterId: string) => `/knowledge/content-filters/${filterId}/validate`,
    // Get filter by source config
    sourceFilter: (configId: string) => `/knowledge/sources/${configId}/content-filter`,
  },

  // Document Splitter Management
  documentSplitters: {
    list: '/knowledge/document-splitters',
    create: '/knowledge/document-splitters',
    splitter: (splitterId: string) => `/knowledge/document-splitters/${splitterId}`,
    update: (splitterId: string) => `/knowledge/document-splitters/${splitterId}`,
    delete: (splitterId: string) => `/knowledge/document-splitters/${splitterId}`,
    defaults: '/knowledge/document-splitters/defaults',
    mostUsed: '/knowledge/document-splitters/most-used',
    usage: (splitterId: string) => `/knowledge/document-splitters/${splitterId}/usage`,
  },

  // Pipeline Management
  pipelines: {
    list: '/pipelines',
    create: '/pipelines',
    pipeline: (pipelineId: string) => `/pipelines/${pipelineId}`,
    update: (pipelineId: string) => `/pipelines/${pipelineId}`,
    delete: (pipelineId: string) => `/pipelines/${pipelineId}`,
    execute: (pipelineId: string) => `/pipelines/${pipelineId}/execute`,
    status: (pipelineId: string) => `/pipelines/${pipelineId}/status`,
  },

  // Unified Model Providers Management
  modelProviders: {
    list: '/providers',
    create: '/providers',
    get: (providerId: string) => `/providers/${providerId}`,
    update: (providerId: string) => `/providers/${providerId}`,
    delete: (providerId: string) => `/providers/${providerId}`,
    test: '/providers/test',
    testById: (providerId: string) => `/providers/${providerId}/test`,
    models: (providerId: string, modelType?: string) =>
      modelType
        ? `/providers/${providerId}/models?model_type=${modelType}`
        : `/providers/${providerId}/models`,
  },
  // LiteLLM Metadata
  litellmProviders: {
    list: '/litellm-providers',
    models: (providerName: string, modelType?: string) => {
      // Safety check: prevent double slashes from empty provider names
      const validProviderName = (providerName || '').trim();
      if (!validProviderName) {
        // Return a placeholder that will result in 404, but won't cause routing issues
        return '/litellm-providers/_invalid_/models';
      }
      return modelType
        ? `/litellm-providers/${validProviderName}/models?model_type=${modelType}`
        : `/litellm-providers/${validProviderName}/models`;
    },
  },

  // Notifications
  notifications: {
    list: '/notifications',
    create: '/notifications',
    notification: (notificationId: string) => `/notifications/${notificationId}`,
    markRead: (notificationId: string) => `/notifications/${notificationId}/read`,
    dismiss: (notificationId: string) => `/notifications/${notificationId}/dismiss`,
    readAll: '/notifications/read-all',
    stats: '/notifications/stats/summary',
    sessionNotifications: (sessionId: string) => `/notifications/session/${sessionId}/notifications`,
    progress: '/notifications/progress',
    updateProgress: (notificationId: string) => `/notifications/progress/${notificationId}`,
    cleanup: '/notifications/cleanup/expired',
    // WebSocket endpoints
    websocket: {
      general: '/ws/notifications',
      session: (sessionId: string) => `/ws/notifications/${sessionId}`,
    },
  },

  // Legacy WebSocket endpoints (deprecated - use structured endpoints above)
  websocket: {
    knowledgeSearch: '/ws/knowledge/search',
    notifications: '/ws/notifications',
    sessionNotifications: (sessionId: string) => `/ws/notifications/${sessionId}`,
  },
};

export const app = {
  name: import.meta.env.APP_NAME || 'dataPilotFlow',
  version: import.meta.env.APP_VERSION || '1.0.0',
  apiBaseUrl: buildApiBaseUrl(),
  redirectQueryParamName: 'r',
  accessTokenStoreKey: 'jwt_token',
  environment: currentEnv,
  isDevelopment,
  isProduction,
  debugMode: import.meta.env.DEBUG_MODE === 'true',
  logLevel: import.meta.env.LOG_LEVEL || 'info',
  // WebSocket configuration
  ws: {
    reconnectAttempts: parseInt(import.meta.env.WS_RECONNECT_ATTEMPTS || '3'),
    reconnectDelay: parseInt(import.meta.env.WS_RECONNECT_DELAY || '2000'),
  },
};

// API utility functions
export const apiUtils = {
  /**
   * Builds a full API URL from an endpoint
   * @param endpoint - The API endpoint (e.g., '/interview/resumes')
   * @returns Full URL with base URL
   */
  buildApiUrl: (endpoint: string): string => {
    const baseUrl = app.apiBaseUrl.replace(/\/$/, ''); // Remove trailing slash
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
  },

  /**
   * Gets the authorization header with JWT token
   * @returns Authorization header object
   */
  getAuthHeaders: (): Record<string, string> => {
    const token = localStorage.getItem(app.accessTokenStoreKey);
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  },

  /**
   * Makes an authenticated API request
   * @param endpoint - The API endpoint
   * @param options - Fetch options
   * @returns Promise with response
   */
  apiRequest: async (endpoint: string, options: RequestInit = {}) => {
    const url = apiUtils.buildApiUrl(endpoint);
    const headers = {
      ...apiUtils.getAuthHeaders(),
      ...options.headers,
    };

    return fetch(url, {
      ...options,
      headers,
    });
  },

  /**
   * Builds a WebSocket URL from an endpoint
   * @param endpoint - The WebSocket endpoint (e.g., '/conversations/ws/{id}/search')
   * @param token - JWT token for authentication
   * @returns Full WebSocket URL
   */
  buildWebSocketUrl: (endpoint: string, token?: string): string => {
    const baseUrl = app.apiBaseUrl.replace(/\/$/, '').replace('http', 'ws');
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const authParam = token ? `?token=${token}` : '';
    return `${baseUrl}${cleanEndpoint}${authParam}`;
  },
};
