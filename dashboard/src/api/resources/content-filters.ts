import { apiEndpoints } from '@/config';
import { z } from 'zod';
import {
  createDeleteMutationHook,
  createGetQueryHook,
  createPostMutationHook,
  createPutMutationHook,
} from '../helpers';

// Zod schemas for Content Filters
export const LLMContentFilterConfigSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  enabled: z.boolean(),
  llm_provider_id: z.string(),
  llm_model_name: z.string(),
  instruction: z.string(),
  chunk_token_threshold: z.number(),
  temperature: z.number().nullable().optional(),
  max_retries: z.number(),
  timeout_seconds: z.number(),
  verbose: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const LLMContentFilterConfigCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  enabled: z.boolean().default(true),
  llm_provider_id: z.string().min(1, 'LLM provider is required'),
  llm_model_name: z.string().min(1, 'LLM model name is required'),
  instruction: z.string().default(`# Content Extraction Instructions

## Objective
Extract all relevant technical documentation content from the page while preserving markdown structure.

## Content to Include

### Headers and Structure
- All headings and subheadings (H1, H2, H3, etc.)
- Maintain hierarchical structure
- Preserve header relationships

### Technical Content
- Paragraphs with technical information
- Code examples and snippets
- Configuration details
- API documentation
- Step-by-step instructions
- Troubleshooting information
- Feature descriptions
- Requirements and prerequisites

## Formatting Requirements
- Keep the content structure intact
- Preserve markdown formatting
- Maintain header hierarchy
- Use proper markdown syntax

## Content to Exclude
- Navigation elements
- Advertisements
- Unrelated content
- Footer information
- Sidebar content`),
  chunk_token_threshold: z.number().min(100).max(4000).default(500),
  temperature: z.number().min(0).max(2).default(0).optional(),
  max_retries: z.number().min(1).max(10).default(3),
  timeout_seconds: z.number().min(10).max(300).default(30),
  verbose: z.boolean().default(false),
});

export const LLMContentFilterConfigUpdateSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  enabled: z.boolean().optional(),
  llm_provider_id: z.string().optional(),
  llm_model_name: z.string().optional(),
  instruction: z.string().optional(),
  chunk_token_threshold: z.number().min(100).max(4000).optional(),
  temperature: z.number().min(0).max(2).optional(),
  max_retries: z.number().min(1).max(10).optional(),
  timeout_seconds: z.number().min(10).max(300).optional(),
  verbose: z.boolean().optional(),
});

export type LLMContentFilterConfig = z.infer<typeof LLMContentFilterConfigSchema>;
export type LLMContentFilterConfigCreate = z.infer<typeof LLMContentFilterConfigCreateSchema>;
export type LLMContentFilterConfigUpdate = z.infer<typeof LLMContentFilterConfigUpdateSchema>;

// Query hooks
export const useGetContentFilters = () =>
  createGetQueryHook<z.ZodArray<typeof LLMContentFilterConfigSchema>, {}, {}>({
    endpoint: apiEndpoints.contentFilters.list,
    responseSchema: z.array(LLMContentFilterConfigSchema),
    rQueryParams: {
      queryKey: ['content-filters'],
    },
  })({});

export const useGetContentFilter = (filterId: string, options?: { enabled?: boolean }) =>
  createGetQueryHook<typeof LLMContentFilterConfigSchema, {}, {}>({
    endpoint: apiEndpoints.contentFilters.filter(filterId),
    responseSchema: LLMContentFilterConfigSchema,
    rQueryParams: {
      queryKey: ['content-filter', { filterId }],
    },
  })({ enabled: options?.enabled !== false && !!filterId });

export const useGetEnabledContentFilters = () =>
  createGetQueryHook<z.ZodArray<typeof LLMContentFilterConfigSchema>, {}, {}>({
    endpoint: `${apiEndpoints.contentFilters.list}?enabled=true`,
    responseSchema: z.array(LLMContentFilterConfigSchema),
    rQueryParams: {
      queryKey: ['content-filters-enabled'],
    },
  })({});

// Mutation hooks
export const useCreateContentFilter = createPostMutationHook<
  typeof LLMContentFilterConfigCreateSchema,
  typeof LLMContentFilterConfigSchema
>({
  endpoint: apiEndpoints.contentFilters.create,
  bodySchema: LLMContentFilterConfigCreateSchema,
  responseSchema: LLMContentFilterConfigSchema,
});

export const useUpdateContentFilter = (filterId: string) =>
  createPutMutationHook<typeof LLMContentFilterConfigUpdateSchema, typeof LLMContentFilterConfigSchema>({
    endpoint: apiEndpoints.contentFilters.update(filterId),
    bodySchema: LLMContentFilterConfigUpdateSchema,
    responseSchema: LLMContentFilterConfigSchema,
  });

export const useDeleteContentFilter = (filterId: string) =>
  createDeleteMutationHook({
    endpoint: apiEndpoints.contentFilters.delete(filterId),
  });

