import { createContext, ReactNode, useEffect, useMemo, useState, useContext } from 'react';
import { loadAccessToken, getStoredToken, removeClientAccessToken } from '@/api/axios';
import { getAccountInfo } from '@/api/resources';

interface AuthContextValues {
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean; // Add loading state
  setIsAuthenticated: (isAuthenticated: boolean) => void;
}

export const AuthContext = createContext<AuthContextValues | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // Add loading state

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true); // Start loading
      try {
        // Check if we have a stored token
        const storedToken = getStoredToken();
        
        if (!storedToken) {
          setIsAuthenticated(false);
          setIsInitialized(true);
          setIsLoading(false);
          return;
        }

        // Load the token into axios headers
        loadAccessToken();

        // Verify the token is valid by calling the API
        try {
          await getAccountInfo();
          
          // If we get here, the token is valid
          setIsAuthenticated(true);
        } catch (apiError: any) {
          // Check if it's a 401 error (invalid token)
          if (apiError?.response?.status === 401) {
            // Clear the invalid token
            removeClientAccessToken();
          }
          
          // Token is invalid or expired, clear it
          setIsAuthenticated(false);
        }
      } catch (error) {
        // Token is invalid or expired, clear it
        setIsAuthenticated(false);
      } finally {
        setIsInitialized(true);
        setIsLoading(false); // End loading
      }
    };

    initializeAuth();
  }, []);

  const value = useMemo(
    () => ({ 
      isAuthenticated, 
      isInitialized,
      isLoading, // Add loading to context
      setIsAuthenticated: (auth: boolean) => {
        setIsAuthenticated(auth);
      }
    }),
    [isAuthenticated, isInitialized, isLoading]
  );

  // Block rendering until authentication is initialized - moved after all hooks
  if (!isInitialized || isLoading) {
    return <div>Loading authentication...</div>;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
