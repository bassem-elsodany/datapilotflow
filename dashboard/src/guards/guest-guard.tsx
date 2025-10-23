import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { LoadingScreen } from '@/components/loading-screen';
import { useAuth } from '@/hooks';
import { app } from '@/config';
import { paths } from '@/routes';

interface GuestGuardProps {
  children: ReactNode;
}

function getRedirectPath(search: string): string {
  const params = new URLSearchParams(search);
  const redirectPath = params.get(app.redirectQueryParamName);
  return redirectPath || paths.dashboard.root;
}

export function GuestGuard({ children }: GuestGuardProps) {
  const { search } = useLocation();
  
  try {
    const { isAuthenticated, isInitialized } = useAuth();

    if (!isInitialized) {
      return <LoadingScreen />;
    }

    if (isAuthenticated) {
      const redirectPath = getRedirectPath(search);
      return <Navigate to={redirectPath} replace />;
    }

    return children;
  } catch (error) {
    // If there's an error with useAuth, show loading screen
    return <LoadingScreen />;
  }
}
