import { SidebarProvider } from '@/contexts/sidebar-context';
import { AuthGuard } from '@/guards/auth-guard';
import { GuestGuard } from '@/guards/guest-guard';
import { PermissionGuard } from '@/guards/permission-guard';
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
            element: <Navigate to={paths.dashboard.apps.agents} replace />,
          },
        ],
      },
      {
        path: paths.dashboard.apps.agents,
        element: (
          <PermissionGuard permission="conversation:read">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/knowledge-search'))}
          </PermissionGuard>
        ),
      },
      {
        path: '/dashboard/apps/agents/create',
        element: (
          <PermissionGuard permission="conversation:manage">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-create'))}
          </PermissionGuard>
        ),
      },
      {
        path: '/dashboard/apps/agents/:agentId/edit',
        element: (
          <PermissionGuard permission="conversation:manage">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-create'))}
          </PermissionGuard>
        ),
      },
      {
        path: '/dashboard/apps/agents/:agentId/conversations',
        element: (
          <PermissionGuard permission="conversation:read">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/agent-conversations'))}
          </PermissionGuard>
        ),
      },
      {
        path: paths.dashboard.apps.conversations,
        element: (
          <PermissionGuard permission="conversation:read">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/all-conversations'))}
          </PermissionGuard>
        ),
      },
      {
        path: paths.dashboard.apps.conversationCreate,
        element: (
          <PermissionGuard permission="conversation:manage">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-create'))}
          </PermissionGuard>
        ),
      },
      {
        path: '/dashboard/apps/conversations/:sessionId',
        element: (
          <PermissionGuard permission="conversation:read">
            {LazyPage(() => import('@/pages/dashboard/apps/knowledge/conversation-window'))}
          </PermissionGuard>
        ),
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
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge/status'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledge.vectorStatus,
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge/vector-status'))}
                  </PermissionGuard>
                ),
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
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/configs'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledgeSources.config(':configId'),
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-details'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledgeSources.configCreate,
                element: (
                  <PermissionGuard permission="knowledge:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-create'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledgeSources.configEdit(':configId'),
                element: (
                  <PermissionGuard permission="knowledge:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/config-edit'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledgeSources.jobs,
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/jobs'))}
                  </PermissionGuard>
                ),
              },
              {
                path: paths.dashboard.management.knowledgeSources.jobCreate,
                element: (
                  <PermissionGuard permission="knowledge:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-create'))}
                  </PermissionGuard>
                ),
              },
              {
                path: '/dashboard/management/knowledge-sources/job-details/:jobId',
                element: (
                  <PermissionGuard permission="knowledge:read">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-details'))}
                  </PermissionGuard>
                ),
              },
              {
                path: '/dashboard/management/knowledge-sources/job-edit/:jobId',
                element: (
                  <PermissionGuard permission="knowledge:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/knowledge-sources/job-edit'))}
                  </PermissionGuard>
                ),
              },
            ],
          },
          /* ---------------------------- MODEL PROVIDERS --------------------------- */
          {
            path: 'model-providers',
            children: [
              {
                index: true,
                element: (
                  <PermissionGuard permission="models:read">
                    {LazyPage(() => import('@/pages/dashboard/management/model-providers'))}
                  </PermissionGuard>
                ),
              },
              {
                path: 'create',
                element: (
                  <PermissionGuard permission="models:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/model-providers/create'))}
                  </PermissionGuard>
                ),
              },
              {
                path: ':providerId/edit',
                element: (
                  <PermissionGuard permission="models:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/model-providers/edit'))}
                  </PermissionGuard>
                ),
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
                element: (
                  <PermissionGuard permission="user:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/users/list'))}
                  </PermissionGuard>
                ),
              },
              {
                path: ':userId/edit',
                element: (
                  <PermissionGuard permission="user:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/users/edit'))}
                  </PermissionGuard>
                ),
              },
              {
                path: 'profile',
                element: LazyPage(() => import('@/pages/dashboard/management/users/profile')),
              },
              {
                path: 'roles',
                element: (
                  <PermissionGuard permission="user:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/users/roles'))}
                  </PermissionGuard>
                ),
              },
              {
                path: 'roles/:roleId/edit',
                element: (
                  <PermissionGuard permission="user:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/users/role-edit'))}
                  </PermissionGuard>
                ),
              },
            ],
          },
          /* ---------------------------- TOOLS MANAGEMENT --------------------------- */
          {
            path: 'tools',
            children: [
              {
                index: true,
                element: (
                  <PermissionGuard permission="tools:read">
                    {LazyPage(() => import('@/pages/dashboard/management/tools'))}
                  </PermissionGuard>
                ),
              },
              {
                path: 'create',
                element: (
                  <PermissionGuard permission="tools:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/tools/form'))}
                  </PermissionGuard>
                ),
              },
              {
                path: ':toolId/edit',
                element: (
                  <PermissionGuard permission="tools:manage">
                    {LazyPage(() => import('@/pages/dashboard/management/tools/form'))}
                  </PermissionGuard>
                ),
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
