/**
 * Deep Agent Types
 * 
 * Type definitions for deep agent state and UI components.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: string;
  status: 'pending' | 'running' | 'completed' | 'error' | 'interrupted';
  duration?: number;  // Execution duration in milliseconds
}

export interface SubAgent {
  id: string;
  name: string;
  subAgentName: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  status: 'pending' | 'active' | 'completed' | 'error';
}

export interface FileItem {
  path: string;
  content: string;
}

/**
 * File metadata from Deep Agents backend
 */
export interface FileMetadata {
  content: string[];  // Array of lines
  created_at: string;
  modified_at: string;
}

/**
 * Files can be either:
 * - Simple string content (legacy)
 * - Array of strings (lines)
 * - Object with metadata (Deep Agents format)
 */
export type FileContent = string | string[] | FileMetadata;

export interface TodoItem {
  id: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  updatedAt?: Date;
}

export interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

export interface ReviewConfig {
  actionName: string;
  allowedDecisions?: string[];
}

export interface ToolApprovalInterruptData {
  action_requests: ActionRequest[];
  review_configs?: ReviewConfig[];
}

/**
 * Deep Agent State Type
 * This represents the state structure from the deep agent graph
 */
export interface DeepAgentState {
  messages: any[];  // LangChain messages
  todos: TodoItem[];
  files: Record<string, FileContent>;
  ui?: any;
}

