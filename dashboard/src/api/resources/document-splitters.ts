import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook, createPutMutationHook } from '../helpers';

// ============================================================================
// DOCUMENT SPLITTER SCHEMAS
// ============================================================================

export const SplitterTypeSchema = z.enum(['text', 'document', 'html']);
export type SplitterType = z.infer<typeof SplitterTypeSchema>;

// Document Splitter Schema
export const DocumentSplitterSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  splitter_type: SplitterTypeSchema,
  chunk_size: z.number().nullable().optional(),
  chunk_overlap: z.number().nullable().optional(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).nullable().optional(),
  sections_to_split_on: z.array(z.tuple([z.string(), z.string()])).nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string(),
  updated_by: z.string(),
});

export type DocumentSplitter = z.infer<typeof DocumentSplitterSchema>;

// Document Splitter Create Schema
export const DocumentSplitterCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  splitter_type: SplitterTypeSchema,
  chunk_size: z.number().min(64).optional(),
  chunk_overlap: z.number().min(0).optional(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),
  sections_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),
});

export type DocumentSplitterCreate = z.infer<typeof DocumentSplitterCreateSchema>;

// Document Splitter Update Schema
export const DocumentSplitterUpdateSchema = z.object({
  name: z.string().min(1).optional(),
  description: z.string().optional(),
  splitter_type: SplitterTypeSchema.optional(),
  chunk_size: z.number().min(64).optional(),
  chunk_overlap: z.number().min(0).optional(),
  headers_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),
  sections_to_split_on: z.array(z.tuple([z.string(), z.string()])).optional(),
});

export type DocumentSplitterUpdate = z.infer<typeof DocumentSplitterUpdateSchema>;

// Usage Statistics Schema
export const DocumentSplitterUsageSchema = z.object({
  splitter_id: z.string(),
  splitter_name: z.string(),
  total_usage_count: z.number(),
  jobs_using_splitter: z.number(),
  recent_jobs_count: z.number(),
  is_default: z.boolean(),
  created_at: z.string(),
  last_updated: z.string(),
});

export type DocumentSplitterUsage = z.infer<typeof DocumentSplitterUsageSchema>;

// ============================================================================
// DOCUMENT SPLITTER API HOOKS
// ============================================================================

// List document splitters
export const useGetDocumentSplitters = createGetQueryHook({
  endpoint: apiEndpoints.documentSplitters.list,
  responseSchema: z.array(DocumentSplitterSchema),
  rQueryParams: { queryKey: ['document-splitters'] },
});

// Get default document splitters
export const useGetDefaultDocumentSplitters = createGetQueryHook({
  endpoint: apiEndpoints.documentSplitters.defaults,
  responseSchema: z.array(DocumentSplitterSchema),
  rQueryParams: { queryKey: ['document-splitters', 'defaults'] },
});

// Get most used document splitters
export const useGetMostUsedDocumentSplitters = createGetQueryHook({
  endpoint: apiEndpoints.documentSplitters.mostUsed,
  responseSchema: z.array(DocumentSplitterSchema),
  rQueryParams: { queryKey: ['document-splitters', 'most-used'] },
});

// Get specific document splitter
export const useGetDocumentSplitter = (splitterId: string) => createGetQueryHook({
  endpoint: apiEndpoints.documentSplitters.splitter(splitterId),
  responseSchema: DocumentSplitterSchema,
  rQueryParams: { queryKey: ['document-splitter', { splitterId }] },
})();

// Get splitter usage statistics
export const useGetDocumentSplitterUsage = (splitterId: string) => createGetQueryHook({
  endpoint: apiEndpoints.documentSplitters.usage(splitterId),
  responseSchema: DocumentSplitterUsageSchema,
  rQueryParams: { queryKey: ['document-splitter-usage', { splitterId }] },
})();

// Create document splitter
export const useCreateDocumentSplitter = createPostMutationHook({
  endpoint: apiEndpoints.documentSplitters.create,
  bodySchema: DocumentSplitterCreateSchema,
  responseSchema: DocumentSplitterSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['document-splitters'] });
    },
  },
});

// Update document splitter
export const useUpdateDocumentSplitter = createPutMutationHook({
  endpoint: apiEndpoints.documentSplitters.splitter(':splitterId'),
  bodySchema: DocumentSplitterUpdateSchema,
  responseSchema: DocumentSplitterSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['document-splitters'] });
      queryClient.invalidateQueries({ queryKey: ['document-splitter'] });
    },
  },
});

// Delete document splitter
export const useDeleteDocumentSplitter = createDeleteMutationHook({
  endpoint: apiEndpoints.documentSplitters.splitter(':splitterId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['document-splitters'] });
    },
  },
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

export const getSplitterTypeLabel = (type: SplitterType): string => {
  switch (type) {
    case 'text':
      return 'Text Chunks';
    case 'document':
      return 'Markdown Structure';
    case 'html':
      return 'HTML Structure';
    default:
      return type;
  }
};

export const getSplitterDescription = (splitter: DocumentSplitter): string => {
  if (splitter.description) {
    return splitter.description;
  }

  if (splitter.splitter_type === 'text') {
    const chunkSize = splitter.chunk_size || 256;
    const chunkOverlap = splitter.chunk_overlap || Math.floor(chunkSize * 0.15);
    return `Token-based chunks (${chunkSize} tokens, ${chunkOverlap} overlap)`;
  } else if (splitter.splitter_type === 'document') {
    const headerCount = splitter.headers_to_split_on?.length || 4;
    return `Markdown structure-based splitting (${headerCount} header levels)`;
  } else if (splitter.splitter_type === 'html') {
    const headerCount = splitter.headers_to_split_on?.length || 4;
    return `HTML structure-based splitting (${headerCount} header levels)`;
  }

  return 'Document splitter configuration';
};

export const validateSplitterConfig = (splitter: DocumentSplitterCreate): string[] => {
  const errors: string[] = [];

  if (!splitter.name?.trim()) {
    errors.push('Name is required');
  }

  if (splitter.splitter_type === 'text') {
    if (!splitter.chunk_size) {
      errors.push('Chunk size is required for text splitters');
    } else if (splitter.chunk_size < 64) {
      errors.push('Chunk size must be at least 64 tokens');
    }

    if (splitter.chunk_overlap !== undefined) {
      if (splitter.chunk_overlap < 0) {
        errors.push('Chunk overlap cannot be negative');
      }
      if (splitter.chunk_size && splitter.chunk_overlap >= splitter.chunk_size) {
        errors.push('Chunk overlap must be less than chunk size');
      }
    }
  } else if (splitter.splitter_type === 'document' || splitter.splitter_type === 'html') {
    if (splitter.headers_to_split_on) {
      if (splitter.headers_to_split_on.length === 0) {
        errors.push('At least one header pattern is required for structure-based splitters');
      }

      for (const [pattern, name] of splitter.headers_to_split_on) {
        if (!pattern?.trim() || !name?.trim()) {
          errors.push('Header patterns and names cannot be empty');
        }
      }
    }
  }

  return errors;
};