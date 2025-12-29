import { apiEndpoints } from '@/config';
import { z } from 'zod';
import { createDeleteMutationHook, createGetQueryHook, createPostMutationHook, createPutMutationHook } from '../helpers';

// ============================================================================
// VECTOR DB COLLECTION SCHEMAS
// ============================================================================

// Vector DB Collection Schema
export const VectorDBCollectionSchema = z.object({
  id: z.string(),
  description: z.string().optional(),

  // Embedding model configuration
  embedding_model_provider_id: z.string(),
  embedding_model_name: z.string(),
  vector_dimension: z.number(),


  // Vector database collection name
  collection_name: z.string(),

  // Metadata
  created_at: z.string(),
  created_by: z.string(),
});

export type VectorDBCollection = z.infer<typeof VectorDBCollectionSchema>;

// Vector DB Collection Create Schema
export const VectorDBCollectionCreateSchema = z.object({
  description: z.string().optional(),
  embedding_model_provider_id: z.string(),
  embedding_model_name: z.string(),
  vector_dimension: z.number().min(1).max(4096),
  collection_name: z.string(),
});

export type VectorDBCollectionCreate = z.infer<typeof VectorDBCollectionCreateSchema>;

// Vector DB Collection Update Schema
export const VectorDBCollectionUpdateSchema = z.object({
  description: z.string().optional(),
  embedding_model_provider_id: z.string().optional(),
  embedding_model_name: z.string().optional(),
  vector_dimension: z.number().min(1).max(4096).optional(),
  collection_name: z.string().optional(),
});

export type VectorDBCollectionUpdate = z.infer<typeof VectorDBCollectionUpdateSchema>;

// ============================================================================
// VECTOR DB COLLECTION API HOOKS
// ============================================================================

// List all vector DB collections (Milvus collections for vector-status page)
export const useGetVectorDBCollections = createGetQueryHook({
  endpoint: apiEndpoints.vectordb.collections,
  responseSchema: z.array(VectorDBCollectionSchema),
  rQueryParams: { queryKey: ['vectordb-collections'] },
});

// List all knowledge vector DB collections (for job creation dropdown)
export const useGetKnowledgeVectorDBCollections = createGetQueryHook({
  endpoint: apiEndpoints.vectordb.knowledgeCollections,
  responseSchema: z.array(VectorDBCollectionSchema),
  rQueryParams: { queryKey: ['knowledge-vectordb-collections'] },
});

// Get specific vector DB collection (Milvus collection for vector-status page)
export const useGetVectorDBCollection = (collectionId: string, options?: { enabled?: boolean }) => createGetQueryHook<typeof VectorDBCollectionSchema, {}, {}>({
  endpoint: apiEndpoints.vectordb.collection(collectionId),
  responseSchema: VectorDBCollectionSchema,
  rQueryParams: { queryKey: ['vectordb-collection', { collectionId }] },
})({ enabled: options?.enabled !== false && !!collectionId });

// Get knowledge VectorDB collection configuration (for job view modal)
export const useGetKnowledgeVectorDBCollection = (collectionId: string, options?: { enabled?: boolean }) => createGetQueryHook<typeof VectorDBCollectionSchema, {}, {}>({
  endpoint: apiEndpoints.vectordb.knowledgeCollection(collectionId),
  responseSchema: VectorDBCollectionSchema,
  rQueryParams: { queryKey: ['knowledge-vectordb-collection', { collectionId }] },
})({ enabled: options?.enabled !== false && !!collectionId });

// Create vector DB collection
export const useCreateVectorDBCollection = createPostMutationHook({
  endpoint: apiEndpoints.vectordb.collections,
  bodySchema: VectorDBCollectionCreateSchema,
  responseSchema: VectorDBCollectionSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['vectordb-collections'] });
    },
  },
});

// Update vector DB collection
export const useUpdateVectorDBCollection = createPutMutationHook({
  endpoint: apiEndpoints.vectordb.collection(':collectionId'),
  bodySchema: VectorDBCollectionUpdateSchema,
  responseSchema: VectorDBCollectionSchema,
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['vectordb-collections'] });
      queryClient.invalidateQueries({ queryKey: ['vectordb-collection'] });
    },
  },
});

// Delete vector DB collection
export const useDeleteVectorDBCollection = createDeleteMutationHook({
  endpoint: apiEndpoints.vectordb.collection(':collectionId'),
  rMutationParams: {
    onSuccess: (data, variables, context, queryClient) => {
      queryClient.invalidateQueries({ queryKey: ['vectordb-collections'] });
    },
  },
});

// Check if collection name exists
export const useCheckCollectionName = (collectionName: string) => {
  return createGetQueryHook({
    endpoint: `${apiEndpoints.vectordb.collections}/check-name/${collectionName}`,
    responseSchema: z.object({
      collection_name: z.string(),
      exists: z.boolean(),
      message: z.string(),
    }),
    rQueryParams: { queryKey: ['vectordb-collection-check', { collectionName }] },
  })();
};
