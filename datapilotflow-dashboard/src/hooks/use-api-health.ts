import { useState, useEffect, useCallback } from 'react';
import { apiUtils } from '@/config';

interface HealthFeature {
  name: string;
  status: string;
  details?: Record<string, unknown>;
}

interface HealthResponse {
  service: string;
  version: string;
  status: string;
  features: HealthFeature[];
  timestamp: string;
}

interface ApiHealthState {
  isHealthy: boolean | null;
  isChecking: boolean;
  lastChecked: Date | null;
  error: string | null;
  version: string | null;
  features: HealthFeature[];
}

export function useApiHealth() {
  const [state, setState] = useState<ApiHealthState>({
    isHealthy: null,
    isChecking: false,
    lastChecked: null,
    error: null,
    version: null,
    features: [],
  });

  const checkHealth = useCallback(async () => {
    setState(prev => ({ ...prev, isChecking: true, error: null }));
    
    try {
      const url = apiUtils.buildApiUrl('/health');
      const response = await fetch(url);
      const isHealthyHttp = response.ok;
      let version: string | null = null;
      let features: HealthFeature[] = [];
      let isHealthy = isHealthyHttp;

      if (isHealthyHttp) {
        const data: HealthResponse = await response.json();
        version = data?.version ?? null;
        features = Array.isArray(data?.features) ? data.features : [];
        // Consider unhealthy if any core feature is down
        const coreFailures = features.filter(f => ['database', 'vector_store', 'interview_rest'].includes(f.name) && (f.status === 'down' || f.status === 'disabled'));
        isHealthy = data?.status === 'healthy' && coreFailures.length === 0;
      }

      setState(prev => ({
        ...prev,
        isHealthy,
        isChecking: false,
        lastChecked: new Date(),
        error: null,
        version,
        features,
      }));
      
      return isHealthy;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      setState(prev => ({
        ...prev,
        isHealthy: false,
        isChecking: false,
        lastChecked: new Date(),
        error: errorMessage,
        version: null,
        features: [],
      }));
      
      return false;
    }
  }, []);

  useEffect(() => {
    // Initial health check
    checkHealth();
    
    // Set up periodic health checks every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    
    return () => clearInterval(interval);
  }, [checkHealth]);

  return {
    ...state,
    checkHealth,
  };
}
