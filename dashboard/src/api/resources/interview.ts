import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createDeleteMutationHook, createPutMutationHook } from '../helpers';
import { apiEndpoints } from '@/config';

// ============================================================================
// SCHEMAS
// ============================================================================

// Enhanced Skill Schema
export const SkillSchema = z.object({
  name: z.string(),
  category: z.string().optional(),
  subcategory: z.string().optional(),
  level: z.string().optional(),
  years_experience: z.number().optional(),
  relevance_score: z.number().optional(),
});

// Enhanced Resume Schema with categorized skills
export const EnhancedResumeSchema = z.object({
  candidate_id: z.string(),
  name: z.string(),
  total_experience_years: z.number(),
  current_role: z.string().nullable(),
  current_company: z.string().nullable(),
  technical_skills: z.array(SkillSchema).optional(),
  soft_skills: z.array(SkillSchema).optional(),
  domain_skills: z.array(SkillSchema).optional(),
  programming_languages: z.array(z.object({
    name: z.string(),
    level: z.string().optional(),
    years_experience: z.number().optional(),
    relevance_score: z.number().optional(),
  })).optional(),
  summary: z.object({
    candidate_overview: z.string().optional(),
    key_strengths: z.string().optional(),
    technical_skills: z.string().optional(),
    experience_highlights: z.string().optional(),
    education_certifications: z.string().optional(),
    assessment_insights: z.string().optional(),
  }).optional(),
  analysis_timestamp: z.string(),
  resume_source: z.string(),
});

// Resume Schemas
export const ResumeSchema = z.object({
  candidate_id: z.string(),
  name: z.string(),
  total_experience_years: z.number(),
  current_role: z.string().nullable(),
  current_company: z.string().nullable(),
  technical_skills_count: z.number(),
  projects_count: z.number(),
  education_count: z.number(),
  certifications_count: z.number(),
  analysis_timestamp: z.string(),
  resume_source: z.string(),  // Legacy field
  // Metadata fields
  original_filename: z.string().nullable().optional(),
  file_size: z.number().nullable().optional(),
  file_type: z.string().nullable().optional(),
  upload_timestamp: z.string().nullable().optional(),
  source_type: z.string().nullable().optional(),
  processing_status: z.string().nullable().optional(),
});

export const ResumeListSchema = z.object({
  success: z.boolean(),
  resumes: z.array(ResumeSchema),
  total_count: z.number(),
});

// Job Description Schemas
export const JobDescriptionSchema = z.object({
  id: z.string(),
  title: z.string(),
  department: z.string().nullable(),
  location: z.string().nullable(),
  summary: z.string(),
  company: z.string().nullable(),
  experience_level: z.string().nullable(),
  min_experience_years: z.number().nullable(),
  max_experience_years: z.number().nullable(),
  expected_role_responsibilities: z.union([z.string(), z.array(z.string())]).nullable().optional(),
  expected_profile: z.union([z.string(), z.array(z.string())]).nullable().optional(),
  required_skills: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : item.name || item.text || JSON.stringify(item))
  ),
  preferred_skills: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : item.name || item.text || JSON.stringify(item))
  ),
  nice_to_have_skills: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : item.name || item.text || JSON.stringify(item))
  ),
  responsibilities: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : (item as any).text || (item as any).description || JSON.stringify(item))
  ),
  requirements: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : (item as any).text || (item as any).description || JSON.stringify(item))
  ),
  skill_priorities: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : (item as any).name || (item as any).text || JSON.stringify(item))
  ),
  assessment_focus_areas: z.array(z.union([z.string(), z.object({}).passthrough()])).transform((arr) => 
    arr.map((item) => typeof item === 'string' ? item : (item as any).name || (item as any).text || JSON.stringify(item))
  ),
  company_context: z.object({
    company_name: z.string().nullable(),
    company_description: z.string().nullable().optional(),
    company_location: z.string().nullable().optional(),
    company_website: z.string().nullable().optional(),
    funding_status: z.string().nullable().optional(),
    founded_year: z.number().nullable().optional(),
    employee_count: z.number().nullable().optional(),
    work_culture: z.string().nullable().optional(),
    benefits: z.array(z.string()).optional(),
    growth_opportunities: z.string().nullable().optional(),
    company_values: z.string().nullable().optional(),
    industry: z.string().nullable(),
    company_size: z.string().nullable(),
    tech_stack: z.array(z.string()),
    team_size: z.number().nullable(),
    reporting_structure: z.string().nullable(),
    remote_policy: z.string().nullable(),
  }).optional().nullable(),
  // File metadata fields
  metadata: z.object({
    original_filename: z.string().nullable().optional(),
    file_size: z.number().nullable().optional(),
    file_type: z.string().nullable().optional(),
    upload_timestamp: z.string().nullable().optional(),
    content_type: z.string().nullable().optional(),
    source_type: z.string().nullable().optional(),
    source_url: z.string().nullable().optional(),
    scraping_timestamp: z.string().nullable().optional(),
    processing_status: z.string().nullable().optional(),
    processing_errors: z.array(z.string()).optional(),
    version: z.string().nullable().optional(),
  }).nullable().optional(),
  created_at: z.string().nullable(),
});

export const JobListSchema = z.object({
  jobs: z.array(JobDescriptionSchema),
});

// Interview Schemas
export const InterviewSchema = z.object({
  id: z.string(),
  name: z.string().nullable(),
  candidate: z.string(),
  job: z.string(),
  job_description_id: z.string().nullable(),  // Add job description ID
  company: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  conversation_history: z.array(z.any()).optional(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
});

export const InterviewListSchema = z.object({
  interviews: z.array(InterviewSchema),
  total_count: z.number(),
});

export const InterviewDetailSchema = z.object({
  id: z.string(),
  name: z.string().nullable(),
  state: z.string(),
  candidate: z.any(), // Complex object
  job: z.any(), // Complex object
  
  // Analytics data (fetched separately)
  analytics_id: z.string().optional(),
  analytics: z.record(z.any()).optional(),
  
  // Analytics data is fetched separately via /analytics endpoint
  // Note: Legacy fields like skill_match_analysis, experience_gap_analysis, etc.
  // are now stored in the separate analytics table and accessed via analytics_id
  conversation_history: z.array(z.any()),
  created_at: z.string(),
  updated_at: z.string(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
});

// Search Result Schemas
export const SearchResultSchema = z.object({
  candidates: z.array(z.object({
    candidate_id: z.string(),
    name: z.string(),
    match_score: z.number(),
    skills_matched: z.array(z.string()),
    experience_years: z.number(),
    current_role: z.string().nullable(),
  })),
  total_count: z.number(),
});

export const JobSearchResultSchema = z.object({
  jobs: z.array(z.object({
    job_id: z.string(),
    title: z.string(),
    company: z.string().nullable(),
    match_score: z.number(),
    skills_matched: z.array(z.string()),
    experience_level: z.string().nullable(),
  })),
  total_count: z.number(),
});

// Statistics Schema
export const StatisticsSchema = z.object({
  total_count: z.number(),
  by_domain: z.record(z.number()),
  by_experience_level: z.record(z.number()),
  by_company: z.record(z.number()),
  recent_additions: z.array(z.any()),
});

// ============================================================================
// RESUME API HOOKS
// ============================================================================

export const useGetResumes = createGetQueryHook({
  endpoint: apiEndpoints.interview.resumes,
  responseSchema: ResumeListSchema,
  rQueryParams: { queryKey: ['resumes'] },
});

export const useGetResume = createGetQueryHook({
  endpoint: apiEndpoints.interview.resume(':candidate_id'),
  responseSchema: ResumeSchema,
  rQueryParams: { queryKey: ['resume'] },
});

export const useCreateResume = createPostMutationHook({
  endpoint: apiEndpoints.interview.resumes,
  bodySchema: z.object({
    resume_file: z.any(),
    candidate_id: z.string().optional(),
  }),
  responseSchema: ResumeSchema,
  options: { isMultipart: true },
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
  },
});

export const useDeleteResume = createDeleteMutationHook({
  endpoint: apiEndpoints.interview.resume(':candidate_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
  },
});

// ============================================================================
// JOB API HOOKS
// ============================================================================

export const useGetJobs = createGetQueryHook({
  endpoint: apiEndpoints.interview.jobs,
  responseSchema: JobListSchema,
  rQueryParams: { queryKey: ['jobs'] },
});

export const useGetJob = createGetQueryHook({
  endpoint: apiEndpoints.interview.job(':job_id'),
  responseSchema: JobDescriptionSchema,
  rQueryParams: { queryKey: ['job'] },
});

export const useCreateJob = createPostMutationHook({
  endpoint: apiEndpoints.interview.jobs,
  bodySchema: z.object({
    job_description_file: z.any(),
    job_id: z.string().optional(),
  }),
  responseSchema: JobDescriptionSchema,
  options: { isMultipart: true },
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  },
});

export const useDeleteJob = createDeleteMutationHook({
  endpoint: apiEndpoints.interview.job(':job_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  },
});

// ============================================================================
// SESSIONS API HOOKS
// ============================================================================

export const useGetInterviews = createGetQueryHook({
  endpoint: apiEndpoints.interview.interviews,
  responseSchema: InterviewListSchema,
  rQueryParams: { queryKey: ['interviews'] },
});

export const useGetInterview = createGetQueryHook({
  endpoint: apiEndpoints.interview.interview(':interview_id'),
  responseSchema: InterviewDetailSchema,
  rQueryParams: { queryKey: ['interview', { interview_id: ':interview_id' }] },
});

export const useCreateInterview = createPostMutationHook({
  endpoint: apiEndpoints.interview.interviews,
  bodySchema: z.object({
    job_description_file: z.any(),
    job_id: z.string().optional(),
    interview_name: z.string().optional(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    interview_id: z.string(),
    message: z.string(),
  }),
  options: { isMultipart: true },
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  },
});

export const useDeleteInterview = createDeleteMutationHook({
  endpoint: apiEndpoints.interview.interview(':interview_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  },
});

// ============================================================================
// SESSION ACTIONS API HOOKS
// ============================================================================

export const useAddResumeToInterview = createPostMutationHook({
  endpoint: apiEndpoints.interview.interviewResume(':interview_id'),
  bodySchema: z.object({
    resume_file: z.any(),
    candidate_id: z.string().optional(),
  }),
  responseSchema: z.any(),
  options: { isMultipart: true },
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['interview'] });
    },
  },
});

export const useChatWithInterview = createPostMutationHook({
  endpoint: apiEndpoints.interview.interviewChat(':interview_id'),
  bodySchema: z.object({
    message: z.string(),
  }),
  responseSchema: z.any(),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['interview'] });
    },
  },
});

// ============================================================================
// SEARCH API HOOKS
// ============================================================================

export const useSearchCandidates = createPostMutationHook({
  endpoint: apiEndpoints.interview.searchCandidates,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: SearchResultSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['search-candidates'] });
    },
  },
});

export const useSearchJobs = createPostMutationHook({
  endpoint: apiEndpoints.interview.searchJobs,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: JobSearchResultSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['search-jobs'] });
    },
  },
});

// ============================================================================
// STATISTICS API HOOKS
// ============================================================================

export const useGetCandidateStatistics = createPostMutationHook({
  endpoint: apiEndpoints.interview.statisticsCandidates,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: StatisticsSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['candidate-statistics'] });
    },
  },
});

export const useGetJobStatistics = createPostMutationHook({
  endpoint: apiEndpoints.interview.statisticsJobs,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: StatisticsSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['job-statistics'] });
    },
  },
});

// ============================================================================
// STATUS API HOOKS
// ============================================================================

export const useGetAnalysisStatus = createPostMutationHook({
  endpoint: apiEndpoints.interview.analysisStatus(':analysis_id'),
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: z.object({
    status: z.enum(['pending', 'processing', 'completed', 'failed']),
    progress: z.number(),
    result: z.any().optional(),
    error: z.string().optional(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['analysis-status'] });
    },
  },
});

export const useGetInterviewStatus = createPostMutationHook({
  endpoint: apiEndpoints.interview.interviewStatus(':interview_id'),
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: z.object({
    status: z.enum(['pending', 'processing', 'completed', 'failed']),
    progress: z.number(),
    result: z.any().optional(),
    error: z.string().optional(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['session-status'] });
    },
  },
});

// ============================================================================
// HEALTH API HOOKS
// ============================================================================

export const useGetHealth = createPostMutationHook({
  endpoint: apiEndpoints.interview.health,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: z.object({
    message: z.string(),
    timestamp: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['health'] });
    },
  },
});

export const useGetDatabaseHealth = createPostMutationHook({
  endpoint: apiEndpoints.interview.healthDatabase,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: z.object({
    message: z.string(),
    resume_count: z.number(),
    interview_context_count: z.number(),
    sample_context: z.any().optional(),
    timestamp: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['database-health'] });
    },
  },
});

// ============================================================================
// CONVERSATION API HOOKS
// ============================================================================

export const useSendChatMessage = createPostMutationHook({
  endpoint: apiEndpoints.conversations.chat,
  bodySchema: z.object({
    message: z.string(),
    candidate_id: z.string(),
    role: z.string(),
    seniority: z.string(),
    domain: z.string(),
  }),
  responseSchema: z.object({
    response: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      // Invalidate conversation-related queries
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

export const useResetConversationMemory = createDeleteMutationHook({
  endpoint: apiEndpoints.conversations.memory,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      // Invalidate all conversation-related queries
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      queryClient.invalidateQueries({ queryKey: ['chat'] });
    },
  },
});

// ============================================================================
// KNOWLEDGE API HOOKS
// ============================================================================

export const useSearchKnowledge = createPostMutationHook({
  endpoint: apiEndpoints.knowledge.search,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    results: z.array(z.any()),
    synthesis: z.string().optional(),
    search_query: z.string(),
    result_count: z.number(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-search'] });
    },
  },
});

export const useContextAwareSearch = createPostMutationHook({
  endpoint: apiEndpoints.knowledge.searchContextAware,
  bodySchema: z.object({
    query: z.string(),
    use_llm: z.boolean().default(true),
    create_new_session: z.boolean().default(false),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    results: z.array(z.any()),
    synthesis: z.string().optional(),
    search_query: z.string(),
    context_used: z.boolean(),
    result_count: z.number(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-search'] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

export const useGetConversationSessions = createGetQueryHook({
  endpoint: apiEndpoints.conversations.sessions,
  responseSchema: z.object({
    success: z.boolean(),
    sessions: z.array(z.object({
      session_id: z.string(),
      name: z.string(),
      created_at: z.string(),
      message_count: z.number(),
      topics_discussed: z.array(z.string()),
      knowledge_sources_used: z.array(z.string()),
    })),
    total_count: z.number(),
  }),
  rQueryParams: { queryKey: ['conversation-sessions'] },
});

export const useGetConversationSession = createGetQueryHook({
  endpoint: apiEndpoints.conversations.session(':session_id'),
  responseSchema: z.object({
    success: z.boolean(),
    session: z.object({
      session_id: z.string(),
      name: z.string(),
      created_at: z.string(),
      message_count: z.number(),
      topics_discussed: z.array(z.string()),
      knowledge_sources_used: z.array(z.string()),
    }),
    messages: z.array(z.any()),
  }),
  rQueryParams: { queryKey: ['conversation-session'] },
});

export const useCreateConversationSession = createPostMutationHook({
  endpoint: apiEndpoints.conversations.createSession,
  bodySchema: z.object({
    name: z.string().optional(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    session_id: z.string(),
    name: z.string(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversation-sessions'] });
    },
  },
});

export const useDeleteConversationSession = createDeleteMutationHook({
  endpoint: apiEndpoints.conversations.session(':session_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversation-sessions'] });
    },
  },
});

export const useRenameConversationSession = createPutMutationHook({
  endpoint: apiEndpoints.conversations.sessionName(':session_id'),
  bodySchema: z.object({
    new_name: z.string(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    session_id: z.string(),
    new_name: z.string(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversation-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['conversation-session'] });
    },
  },
});

export const useIngestKnowledgeFile = createPostMutationHook({
  endpoint: apiEndpoints.knowledge.ingest,
  bodySchema: z.object({
    file: z.any(),
    user_id: z.string().optional(),
    description: z.string().default(''),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    file_id: z.string(),
    message: z.string(),
    status: z.string(),
  }),
  options: { isMultipart: true },
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-jobs'] });
    },
  },
});

export const useGetKnowledgeFileStatus = createGetQueryHook({
  endpoint: apiEndpoints.knowledge.ingestStatus(':file_id'),
  responseSchema: z.object({
    success: z.boolean(),
    file_id: z.string(),
    status: z.string(),
    progress: z.number(),
    message: z.string(),
    created_at: z.string().optional(),
    completed_at: z.string().optional(),
  }),
  rQueryParams: { queryKey: ['knowledge-file-status'] },
});

export const useGetKnowledgeJobs = createGetQueryHook({
  endpoint: apiEndpoints.knowledge.ingestJobs,
  responseSchema: z.object({
    success: z.boolean(),
    jobs: z.array(z.any()),
    total_count: z.number(),
  }),
  rQueryParams: { queryKey: ['knowledge-jobs'] },
});

// ============================================================================
// QUESTIONS API HOOKS
// ============================================================================

export const useGetQuestions = createGetQueryHook({
  endpoint: apiEndpoints.questions.list,
  responseSchema: z.object({
    success: z.boolean(),
    questions: z.array(z.any()),
    count: z.number(),
    filters: z.object({
      domain: z.string().optional(),
      difficulty: z.string().optional(),
      source: z.string().optional(),
      limit: z.number(),
    }),
  }),
  rQueryParams: { queryKey: ['questions'] },
});

export const useCreateQuestion = createPostMutationHook({
  endpoint: apiEndpoints.questions.create,
  bodySchema: z.any(),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    question: z.any(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
  },
});

export const useGetQuestion = createGetQueryHook({
  endpoint: apiEndpoints.questions.question(':question_id'),
  responseSchema: z.object({
    success: z.boolean(),
    question: z.any(),
  }),
  rQueryParams: { queryKey: ['question'] },
});

export const useUpdateQuestion = createPutMutationHook({
  endpoint: apiEndpoints.questions.question(':question_id'),
  bodySchema: z.any(),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    question: z.any(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      queryClient.invalidateQueries({ queryKey: ['question'] });
    },
  },
});

export const useDeleteQuestion = createDeleteMutationHook({
  endpoint: apiEndpoints.questions.question(':question_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
  },
});

export const useGetDomains = createGetQueryHook({
  endpoint: apiEndpoints.questions.domains,
  responseSchema: z.object({
    success: z.boolean(),
    domains: z.array(z.any()),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['domains'] },
});

export const useCreateDomain = createPostMutationHook({
  endpoint: apiEndpoints.questions.domains,
  bodySchema: z.any(),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    domain: z.any(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
    },
  },
});

export const useGetDomain = createGetQueryHook({
  endpoint: apiEndpoints.questions.domain(':domain_id'),
  responseSchema: z.object({
    success: z.boolean(),
    domain: z.any(),
  }),
  rQueryParams: { queryKey: ['domain'] },
});

export const useUpdateDomain = createPutMutationHook({
  endpoint: apiEndpoints.questions.domain(':domain_id'),
  bodySchema: z.any(),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    domain: z.any(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
      queryClient.invalidateQueries({ queryKey: ['domain'] });
    },
  },
});

export const useDeleteDomain = createDeleteMutationHook({
  endpoint: apiEndpoints.questions.domain(':domain_id'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['domains'] });
    },
  },
});

export const useGetDomainStatistics = createGetQueryHook({
  endpoint: apiEndpoints.questions.domainStats,
  responseSchema: z.object({
    success: z.boolean(),
    statistics: z.object({
      domains: z.any(),
      difficulties: z.any(),
      sources: z.any(),
    }),
  }),
  rQueryParams: { queryKey: ['domain-statistics'] },
});

export const useGetQuestionsByDomain = createGetQueryHook({
  endpoint: apiEndpoints.questions.byDomain(':domain_name'),
  responseSchema: z.object({
    success: z.boolean(),
    questions: z.array(z.any()),
    domain: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['questions-by-domain'] },
});

export const useGetQuestionsByDomainLevel = createGetQueryHook({
  endpoint: apiEndpoints.questions.byDomainLevel(':domain_name', ':level'),
  responseSchema: z.object({
    success: z.boolean(),
    questions: z.array(z.any()),
    domain: z.string(),
    difficulty: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['questions-by-domain-level'] },
});

export const useGetDifficultyLevels = createGetQueryHook({
  endpoint: apiEndpoints.questions.difficultyLevels,
  responseSchema: z.object({
    success: z.boolean(),
    difficulty_levels: z.array(z.string()),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['difficulty-levels'] },
});

export const useCreateSampleData = createPostMutationHook({
  endpoint: apiEndpoints.questions.sampleData,
  bodySchema: z.object({}),
  responseSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    created: z.any(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      queryClient.invalidateQueries({ queryKey: ['domains'] });
    },
  },
});

// ============================================================================
// SMART FEATURES API HOOKS
// ============================================================================

export const useGenerateProjectBasedQuestion = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.questions.generateProjectBased,
  bodySchema: z.object({
    project_context: z.any(),
    candidate_skills: z.array(z.string()),
    experience_level: z.string(),
    previous_responses: z.array(z.string()).optional(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    custom_question: z.any(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['custom-questions'] });
    },
  },
});

export const useGenerateSkillGapQuestion = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.questions.generateSkillGap,
  bodySchema: z.object({
    skill_gap: z.any(),
    candidate_skills: z.array(z.string()),
    experience_level: z.string(),
    previous_responses: z.array(z.string()).optional(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    custom_question: z.any(),
    message: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['custom-questions'] });
    },
  },
});

export const useGetCustomQuestion = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.questions.custom(':question_id'),
  responseSchema: z.object({
    success: z.boolean(),
    custom_question: z.any(),
  }),
  rQueryParams: { queryKey: ['custom-question'] },
});

export const useGetCustomQuestionsByType = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.questions.customByType(':generation_type'),
  responseSchema: z.object({
    success: z.boolean(),
    custom_questions: z.array(z.any()),
    generation_type: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['custom-questions-by-type'] },
});

export const useGetTimeAwareQuestionSelection = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.selection.timeAware,
  bodySchema: z.any(),
  responseSchema: z.object({
    success: z.boolean(),
    selected_questions: z.array(z.any()),
    selection_criteria: z.any(),
    count: z.number(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['time-aware-selection'] });
    },
  },
});

export const useGenerateRecommendations = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.recommendations.generate,
  bodySchema: z.object({
    candidate_id: z.string(),
    candidate_skills: z.array(z.string()),
    experience_level: z.string(),
    previous_performance: z.record(z.number()),
    strengths: z.array(z.string()),
    weaknesses: z.array(z.string()),
    interview_stage: z.string(),
    time_remaining: z.number(),
    domains_covered: z.array(z.string()),
    domains_remaining: z.array(z.string()),
    recent_questions: z.array(z.string()),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    recommendations: z.array(z.any()),
    candidate_id: z.string(),
    count: z.number(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  },
});

export const useGetRecommendation = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.recommendations.recommendation(':recommendation_id'),
  responseSchema: z.object({
    success: z.boolean(),
    recommendation: z.any(),
  }),
  rQueryParams: { queryKey: ['recommendation'] },
});

export const useGetRecommendationsByPriority = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.recommendations.byPriority,
  responseSchema: z.object({
    success: z.boolean(),
    recommendations: z.array(z.any()),
    min_priority: z.number(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['recommendations-by-priority'] },
});

export const useGenerateInterviewAnalytics = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.analytics.generate,
  bodySchema: z.object({
    session_id: z.string(),
    candidate_id: z.string(),
    interviewer_id: z.string(),
    session_data: z.any(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    analytics: z.any(),
    session_id: z.string(),
    candidate_id: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  },
});

export const useGetSessionAnalytics = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.analytics.session(':session_id'),
  responseSchema: z.object({
    success: z.boolean(),
    analytics: z.any(),
    session_id: z.string(),
  }),
  rQueryParams: { queryKey: ['session-analytics'] },
});

export const useGetCandidateAnalytics = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.analytics.candidate(':candidate_id'),
  responseSchema: z.object({
    success: z.boolean(),
    analytics: z.array(z.any()),
    candidate_id: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['candidate-analytics'] },
});

export const useGeneratePerformanceTrend = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.trends.generate,
  bodySchema: z.object({
    candidate_id: z.string(),
    trend_period: z.string().default('month'),
    start_date: z.string().optional(),
    end_date: z.string().optional(),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    trend_data: z.any(),
    candidate_id: z.string(),
    trend_period: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['trends'] });
    },
  },
});

export const useGetCandidateTrends = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.trends.candidate(':candidate_id'),
  responseSchema: z.object({
    success: z.boolean(),
    trends: z.array(z.any()),
    candidate_id: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['candidate-trends'] },
});

export const useGenerateSkillCoverageReport = createPostMutationHook({
  endpoint: apiEndpoints.smartFeatures.reports.coverage.generate,
  bodySchema: z.object({
    candidate_id: z.string(),
    required_skills: z.array(z.string()),
    report_period: z.string().default('Q1 2024'),
  }),
  responseSchema: z.object({
    success: z.boolean(),
    report: z.any(),
    candidate_id: z.string(),
    report_period: z.string(),
  }),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['coverage-reports'] });
    },
  },
});

export const useGetSkillCoverageReport = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.reports.coverage.report(':report_id'),
  responseSchema: z.object({
    success: z.boolean(),
    report: z.any(),
    report_id: z.string(),
  }),
  rQueryParams: { queryKey: ['coverage-report'] },
});

export const useGetCandidateCoverageReports = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.reports.coverage.candidate(':candidate_id'),
  responseSchema: z.object({
    success: z.boolean(),
    reports: z.array(z.any()),
    candidate_id: z.string(),
    count: z.number(),
  }),
  rQueryParams: { queryKey: ['candidate-coverage-reports'] },
});

export const useGetSmartFeaturesDashboard = createGetQueryHook({
  endpoint: apiEndpoints.smartFeatures.dashboard,
  responseSchema: z.object({
    success: z.boolean(),
    dashboard: z.any(),
    user_id: z.string(),
  }),
  rQueryParams: { queryKey: ['smart-features-dashboard'] },
});
