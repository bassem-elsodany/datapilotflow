import { SidebarProvider } from '@/contexts/sidebar-context';
import { AuthGuard } from '@/guards/auth-guard';
import { GuestGuard } from '@/guards/guest-guard';
import { AuthLayout } from '@/layouts/auth';
import { DashboardLayout } from '@/layouts/dashboard';
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { LazyPage } from './lazy-page';
import { paths } from './paths';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to={paths.dashboard.root} replace />,
  },

  /* ---------------------------------- AUTH ---------------------------------- */
  {
    path: paths.auth.root,
    element: (
      <GuestGuard>
        <AuthLayout />
      </GuestGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to={paths.auth.login} replace />,
      },
      {
        path: 'login',
        element: LazyPage(() => import('@/pages/auth/login')),
      },
      {
        path: 'register',
        element: LazyPage(() => import('@/pages/auth/register')),
      },
      {
        path: 'forgot-password',
        element: LazyPage(() => import('@/pages/auth/forgot-password')),
      },

    ],
  },

  {
    path: paths.dashboard.root,
    element: (
      <AuthGuard>
        <SidebarProvider>
          <DashboardLayout />
        </SidebarProvider>
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        path: paths.dashboard.root,
        element: <Navigate to={paths.dashboard.home} replace />,
      },
      {
        path: paths.dashboard.home,
        element: LazyPage(() => import('@/pages/dashboard/home')),
      },
      /* ---------------------------------- APPS ---------------------------------- */
      {
        path: paths.dashboard.apps.root,
        children: [
          {
            index: true,
            path: paths.dashboard.apps.root,
            element: <Navigate to={paths.dashboard.apps.knowledgeSearch} replace />,
          },
        ],
      },
      {
        path: paths.dashboard.apps.knowledgeSearch,
        element: LazyPage(() => import('@/pages/dashboard/apps/knowledge/knowledge-search')),
      },
      {
        path: paths.dashboard.apps.conversationCreate,
        element: LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-create')),
      },
      {
        path: '/dashboard/apps/conversation/:sessionId',
        element: LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-window')),
      },
      /* ------------------------------- MANAGEMENT ------------------------------- */
      {
        path: paths.dashboard.management.root,
        children: [
          {
            index: true,
            path: paths.dashboard.management.root,
            element: <Navigate to={paths.dashboard.management.knowledge.root} replace />,
          },
          {
            path: paths.dashboard.management.knowledge.root,
            children: [
              {
                index: true,
                path: paths.dashboard.management.knowledge.root,
                element: <Navigate to={paths.dashboard.management.knowledge.status} replace />,
              },
              {
                path: paths.dashboard.management.knowledge.status,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge/status')),
              },
              {
                path: paths.dashboard.management.knowledge.vectorStatus,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge/vector-status')),
              },
            ],
          },
          /* ---------------------------- RAG CONFIGURATION MANAGEMENT --------------------------- */
          {
            path: paths.dashboard.management.knowledgeSources.root,
            children: [
              {
                index: true,
                path: paths.dashboard.management.knowledgeSources.root,
                element: <Navigate to={paths.dashboard.management.knowledgeSources.configs} replace />,
              },
              {
                path: paths.dashboard.management.knowledgeSources.configs,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/configs')),
              },
              {
                path: paths.dashboard.management.knowledgeSources.config(':configId'),
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-details')),
              },
              {
                path: paths.dashboard.management.knowledgeSources.configCreate,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-create')),
              },
              {
                path: paths.dashboard.management.knowledgeSources.configEdit(':configId'),
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-edit')),
              },
              {
                path: paths.dashboard.management.knowledgeSources.jobs,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/jobs')),
              },
              {
                path: paths.dashboard.management.knowledgeSources.jobCreate,
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-create')),
              },
              {
                path: '/dashboard/management/knowledge-sources/job-details/:jobId',
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-details')),
              },
              {
                path: '/dashboard/management/knowledge-sources/job-edit/:jobId',
                element: LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-edit')),
              },
            ],
          },
          /* ---------------------------- PIPELINE BUILDER --------------------------- */
          {
            path: paths.dashboard.management.pipelineBuilder.root,
            element: LazyPage(() => import('@/pages/dashboard/management/pipeline-builder')),
          },
          /* ---------------------------- MODEL PROVIDERS --------------------------- */
          {
            path: 'model-providers',
            children: [
              {
                index: true,
                element: LazyPage(() => import('@/pages/dashboard/management/model-providers')),
              },
            ],
          },
          /* ---------------------------- USER MANAGEMENT --------------------------- */
          {
            path: 'users',
            children: [
              {
                index: true,
                element: <Navigate to="list" replace />,
              },
              {
                path: 'list',
                element: LazyPage(() => import('@/pages/dashboard/management/users/list')),
              },
              {
                path: ':userId/edit',
                element: LazyPage(() => import('@/pages/dashboard/management/users/edit')),
              },
              {
                path: 'profile',
                element: LazyPage(() => import('@/pages/dashboard/management/users/profile')),
              },
              {
                path: 'roles',
                element: LazyPage(() => import('@/pages/dashboard/management/users/roles')),
              },
              {
                path: 'roles/:roleId/edit',
                element: LazyPage(() => import('@/pages/dashboard/management/users/role-edit')),
              },
            ],
          },
        ],
      },
    ],
  },
]);

export function Router() {
  return <RouterProvider router={router} />;
}
