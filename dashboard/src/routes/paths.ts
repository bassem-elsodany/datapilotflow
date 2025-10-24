export const paths = {
  auth: {
    root: '/auth',
    login: '/auth/login',
    register: '/auth/register',
    forgotPassword: '/auth/forgot-password',
    resetPassword: '/auth/reset-password',
    otp: '/auth/otp',
    terms: '/auth/terms',
    privacy: '/auth/privacy',
  },

  dashboard: {
    root: '/dashboard',
    home: '/dashboard/home',
    management: {
      root: '/dashboard/management',
      knowledge: {
        root: '/dashboard/management/knowledge',
        status: '/dashboard/management/knowledge/status',
        vectorStatus: '/dashboard/management/knowledge/vector-status',
      },
      knowledgeSources: {
        root: '/dashboard/management/knowledge-sources',
        configs: '/dashboard/management/knowledge-sources/configs',
        config: (configId: string) => `/dashboard/management/knowledge-sources/configs/${configId}`,
        configCreate: '/dashboard/management/knowledge-sources/configs/create',
        configEdit: (configId: string) => `/dashboard/management/knowledge-sources/configs/${configId}/edit`,
        jobs: '/dashboard/management/knowledge-sources/jobs',
        job: (jobId: string) => `/dashboard/management/knowledge-sources/job-details/${jobId}`,
        jobCreate: '/dashboard/management/knowledge-sources/job-create',
        jobEdit: (jobId: string) => `/dashboard/management/knowledge-sources/job-edit/${jobId}`,
      },
      pipelineBuilder: {
        root: '/dashboard/management/pipeline-builder',
      },
      modelProviders: {
        root: '/dashboard/management/model-providers',
        list: '/dashboard/management/model-providers',
        provider: (providerId: string) => `/dashboard/management/model-providers/${providerId}`,
        providerEdit: (providerId: string) => `/dashboard/management/model-providers/${providerId}/edit`,
        providerCreate: '/dashboard/management/model-providers/create',
      },
      users: {
        root: '/dashboard/management/users',
        list: '/dashboard/management/users/list',
        create: '/dashboard/management/users/create',
        edit: (userId: string) => `/dashboard/management/users/${userId}/edit`,
        profile: '/dashboard/management/users/profile',
        roles: '/dashboard/management/users/roles',
        roleCreate: '/dashboard/management/users/roles/create',
        roleEdit: (roleId: string) => `/dashboard/management/users/roles/${roleId}/edit`,
      },
    },
    apps: {
      root: '/dashboard/apps',
      knowledgeSearch: '/dashboard/apps/knowledge-search',
      conversationCreate: '/dashboard/apps/conversation/create',
      conversation: (sessionId: string) => `/dashboard/apps/conversation/${sessionId}`,
    },
  },
};
