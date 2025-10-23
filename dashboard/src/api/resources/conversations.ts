import { z } from 'zod';
import { createGetQueryHook, createPostMutationHook, createPutMutationHook, createDeleteMutationHook } from '../helpers';
import { apiEndpoints } from '../../config';

// Conversation Schema
export const ConversationSchema = z.object({
  id: z.string(),
  name: z.string(),
  created_at: z.string(),
  message_count: z.number(),
  topics_discussed: z.array(z.string()),
  knowledge_sources_used: z.array(z.string()),
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

// Create new conversation
export const useCreateConversation = createPostMutationHook({
  endpoint: '/conversations',
  bodySchema: CreateSessionRequestSchema,
  responseSchema: CreateSessionResponseSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  },
});

// Delete conversation
export const useDeleteConversation = createDeleteMutationHook({
  endpoint: '/conversations/:conversationId',
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
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
    onSuccess: (data, variables, context, queryClient) => {
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
    onSuccess: (data, variables, context, queryClient) => {
      // Invalidate the specific conversation to refresh messages
      const conversationId = variables.route?.conversationId;
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
