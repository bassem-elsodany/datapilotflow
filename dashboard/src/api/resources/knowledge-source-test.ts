import { z } from 'zod';
import { client } from '../axios';

// Request schema
export const TestSelectorRequestSchema = z.object({
  url: z.string().url('Invalid URL format'),
  target_elements: z.array(z.string()).default([]),
  scraping_mode: z.enum(['single_page', 'website', 'multiple_pages']).default('single_page'),
  crawl_depth: z.number().int().min(0).max(6).default(0),
  output_format: z.enum(['html', 'markdown', 'llm_markdown']).default('html'),
  content_filter_threshold: z.number().min(0).max(1).optional(),
  llm_instructions: z.string().optional(),
  llm_provider_id: z.string().optional(),
  llm_model_name: z.string().optional(),
});

export type TestSelectorRequest = z.infer<typeof TestSelectorRequestSchema>;

// Response schema
export const TestSelectorResponseSchema = z.object({
  success: z.boolean(),
  url: z.string(),
  target_elements: z.array(z.string()),
  extracted_content: z.string(),
  content_length: z.number(),
  error_message: z.string().nullable().optional(),
  processing_time_ms: z.number(),
});

export type TestSelectorResponse = z.infer<typeof TestSelectorResponseSchema>;

// API functions
export const testCssSelectors = async (request: TestSelectorRequest): Promise<TestSelectorResponse> => {
  const response = await client.post('/knowledge/sources-preview-content/', request, {
    timeout: 60000 // 60 seconds timeout
  });
  return TestSelectorResponseSchema.parse(response.data);
};
