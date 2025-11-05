import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '../helpers';
import { apiEndpoints } from '../../config';

// ============================================================================
// NESTED CONFIGURATION SCHEMAS
// ============================================================================

// Provider Configuration Schema
export const ProviderConfigSchema = z.object({
  id: z.string(),
  model_name: z.string(),
});

export type ProviderConfig = z.infer<typeof ProviderConfigSchema>;

// System Prompt Schema
export const SystemPromptSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
}).optional().nullable();

export type SystemPrompt = z.infer<typeof SystemPromptSchema>;

// Enhancement Configuration Schema
export const EnhancementConfigSchema = z.object({
  strategy: z.string(),
  provider: ProviderConfigSchema.optional().nullable(),
}).optional().nullable();

export type EnhancementConfig = z.infer<typeof EnhancementConfigSchema>;

// Vector Database Configuration Schema
export const VectorDatabaseConfigSchema = z.object({
  collection_name: z.string(),
  top_k: z.number(),
}).optional().nullable();

export type VectorDatabaseConfig = z.infer<typeof VectorDatabaseConfigSchema>;

// Reranker Configuration Schema
export const RerankerConfigSchema = z.object({
  provider: ProviderConfigSchema.optional().nullable(),
  relevance_threshold: z.number(),
}).optional().nullable();

export type RerankerConfig = z.infer<typeof RerankerConfigSchema>;

// Answer Generation Configuration Schema
export const AnswerGenerationConfigSchema = z.object({
  provider: ProviderConfigSchema.optional().nullable(),
}).optional().nullable();

export type AnswerGenerationConfig = z.infer<typeof AnswerGenerationConfigSchema>;

// ============================================================================
// CONVERSATION SCHEMAS
// ============================================================================

// Conversation Schema (with nested configuration)
export const ConversationSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional().nullable(),
  created_at: z.string(),
  message_count: z.number().optional(),
  topics_discussed: z.array(z.string()).optional(),
  knowledge_sources_used: z.array(z.string()).optional(),
  // Nested configuration
  system_prompt: SystemPromptSchema,
  enhancement: EnhancementConfigSchema,
  vector_database: VectorDatabaseConfigSchema,
  reranker: RerankerConfigSchema,
  answer_generation: AnswerGenerationConfigSchema,
  enable_knowledge_assistant: z.boolean().optional(),
  tags: z.array(z.string()).optional(),
});

export type Conversation = z.infer<typeof ConversationSchema>;

// Conversations List Schema
export const ConversationsListSchema = z.object({
  success: z.boolean(),
  sessions: z.array(ConversationSchema),
  total_count: z.number(),
});

export type ConversationsList = z.infer<typeof ConversationsListSchema>;

// Conversation Detail Schema
export const ConversationDetailSchema = z.object({
  success: z.boolean(),
  session: ConversationSchema,
  messages: z.array(z.object({
    role: z.string(),
    content: z.string(),
    timestamp: z.string(),
  })),
});

export type ConversationDetail = z.infer<typeof ConversationDetailSchema>;

// Message Schema
export const MessageSchema = z.object({
  role: z.string(),
  content: z.string(),
  timestamp: z.string(),
});

export type Message = z.infer<typeof MessageSchema>;

// Chat Message Request Schema
export const ChatMessageRequestSchema = z.object({
  message: z.string(),
  candidate_id: z.string(),
  role: z.string(),
  seniority: z.string(),
  domain: z.string(),
});

export type ChatMessageRequest = z.infer<typeof ChatMessageRequestSchema>;

// Chat Response Schema
export const ChatResponseSchema = z.object({
  response: z.string(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;

// Create Session Request Schema
export const CreateSessionRequestSchema = z.object({
  name: z.string().optional(),
});

export type CreateSessionRequest = z.infer<typeof CreateSessionRequestSchema>;

// Create Session Response Schema
export const CreateSessionResponseSchema = z.object({
  success: z.boolean(),
  id: z.string(),
  name: z.string(),
  message: z.string(),
});

export type CreateSessionResponse = z.infer<typeof CreateSessionResponseSchema>;

// Rename Session Request Schema
export const RenameSessionRequestSchema = z.object({
  new_name: z.string(),
});

export type RenameSessionRequest = z.infer<typeof RenameSessionRequestSchema>;

// Rename Session Response Schema
export const RenameSessionResponseSchema = z.object({
  success: z.boolean(),
  session_id: z.string(),
  new_name: z.string(),
  message: z.string(),
});

export type RenameSessionResponse = z.infer<typeof RenameSessionResponseSchema>;

// ============================================================================
// CREATE/UPDATE CONVERSATION REQUEST SCHEMAS (Nested Structure)
// ============================================================================

// Create Conversation Request with nested configuration
export const CreateConversationRequestSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  system_prompt: SystemPromptSchema.optional(),
  enhancement: EnhancementConfigSchema.optional(),
  vector_database: VectorDatabaseConfigSchema.optional(),
  reranker: RerankerConfigSchema.optional(),
  answer_generation: AnswerGenerationConfigSchema.optional(),
  enable_knowledge_assistant: z.boolean().optional(),
  tags: z.array(z.string()).optional(),
});

export type CreateConversationRequest = z.infer<typeof CreateConversationRequestSchema>;

// Update Conversation Request with nested configuration
export const UpdateConversationRequestSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  system_prompt: SystemPromptSchema.optional(),
  enhancement: EnhancementConfigSchema.optional(),
  vector_database: VectorDatabaseConfigSchema.optional(),
  reranker: RerankerConfigSchema.optional(),
  answer_generation: AnswerGenerationConfigSchema.optional(),
  enable_knowledge_assistant: z.boolean().optional(),
  tags: z.array(z.string()).optional(),
});

export type UpdateConversationRequest = z.infer<typeof UpdateConversationRequestSchema>;

// Update Conversation Response Schema
export const UpdateConversationResponseSchema = z.object({
  success: z.boolean(),
  id: z.string(),
  message: z.string(),
});

export type UpdateConversationResponse = z.infer<typeof UpdateConversationResponseSchema>;

// API Hooks

// List all conversations
export const useGetConversations = createGetQueryHook({
  endpoint: '/conversations',
  responseSchema: ConversationsListSchema,
  rQueryParams: { queryKey: ['conversations'] },
});

// Get specific conversation
export const useGetConversation = (conversationId: string) => createGetQueryHook({
  endpoint: `/conversations/${conversationId}`,
  responseSchema: ConversationDetailSchema,
  rQueryParams: { queryKey: ['conversations', conversationId] },
})();

// Create new conversation (with nested configuration)
export const useCreateConversation = createPostMutationHook({
  endpoint: '/conversations',
  bodySchema: CreateConversationRequestSchema,
  responseSchema: CreateSessionResponseSchema,
  rMutationParams: {
    onSuccess: (_data, _variables, _context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

// Update conversation configuration
export const useUpdateConversation = createPutMutationHook({
  endpoint: '/conversations/:conversationId',
  bodySchema: UpdateConversationRequestSchema,
  responseSchema: UpdateConversationResponseSchema,
  rMutationParams: {
    onSuccess: (_data, variables, _context, queryClient) => {
      const conversationId = (variables as any).route?.conversationId;
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['conversations', conversationId] });
      }
    },
  },
});

// Delete conversation
export const useDeleteConversation = createDeleteMutationHook({
  endpoint: '/conversations/:conversationId',
  rMutationParams: {
    onSuccess: (_data, _variables, _context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

// Rename conversation
export const useRenameConversation = createPutMutationHook({
  endpoint: '/conversations/:conversationId/name',
  bodySchema: RenameSessionRequestSchema,
  responseSchema: RenameSessionResponseSchema,
  rMutationParams: {
    onSuccess: (_data, _variables, _context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

// Send chat message
export const useSendChatMessage = createPostMutationHook({
  endpoint: '/conversations/:conversationId/chat',
  bodySchema: ChatMessageRequestSchema,
  responseSchema: ChatResponseSchema,
  rMutationParams: {
    onSuccess: (_data, variables, _context, queryClient) => {
      // Invalidate the specific conversation to refresh messages
      const conversationId = (variables as any).route?.conversationId;
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['conversations', conversationId] });
      }
    },
  },
});

// Reset conversation messages
export const useResetConversationMessages = createDeleteMutationHook({
  endpoint: '/conversations/:conversationId/messages',
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      // Invalidate the specific conversation to refresh messages
      const conversationId = variables.route?.conversationId;
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: ['conversations', conversationId] });
      }
    },
  },
});
