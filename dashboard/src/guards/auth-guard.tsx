import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { LoadingScreen } from '@/components/loading-screen';
import { useAuth } from '@/hooks';
import { app } from '@/config';
import { paths } from '@/routes';

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { pathname } = useLocation();
  
  try {
    const { isAuthenticated, isInitialized, isLoading } = useAuth();

    if (!isInitialized || isLoading) {
      return <LoadingScreen />;
    }

    if (!isAuthenticated) {
      return (
        <Navigate to={`${paths.auth.login}?${app.redirectQueryParamName}=${pathname}`} replace />
      );
    }

    return children;
  } catch (error) {
    // If there's an error with useAuth, show loading screen
    return <LoadingScreen />;
  }
}
