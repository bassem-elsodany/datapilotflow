/**
 * Conversation RAG Pipeline Templates
 *
 * Pre-built conversation templates with required and optional configuration nodes.
 * Users select a template and customize by enabling/disabling optional components.
 */


export interface ConversationTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  type: 'rag' | 'supervisor'; // Template type: RAG or Supervisor Agent
  requiredNodes: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  optionalNodes: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  defaultConfig: {
    selectedStrategy: string;
    enableReranking: boolean;
    enableLLMGeneration: boolean;
  };
}

export const CONVERSATION_TEMPLATES: ConversationTemplate[] = [
  {
    id: 'basic-rag',
    name: 'Basic RAG Conversation Agent Pipeline',
    description: 'Simple retrieval with optional reranking & LLM generation',
    icon: '📦',
    type: 'rag',
    requiredNodes: [
      {
        id: 'config',
        name: 'Conversation Settings',
        description: 'Name & description',
      },
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'None (native RAG)',
      },
      {
        id: 'retrieval',
        name: 'Document Retrieval',
        description: 'Vector search',
      },
    ],
    optionalNodes: [
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'Rank documents by relevance',
      },
      {
        id: 'llm',
        name: 'Generative Answer',
        description: 'Generate answers with LLM',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'native',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },

  {
    id: 'augmented-rag',
    name: 'Augmented RAG Conversation Agent',
    description: 'Comprehensive query transformation with 4 variants + optional reranking & LLM',
    icon: '✨',
    type: 'rag',
    requiredNodes: [
      {
        id: 'config',
        name: 'Conversation Settings',
        description: 'Name & description',
      },
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'Augmented (4 variants)',
      },
      {
        id: 'retrieval',
        name: 'Document Retrieval',
        description: 'RRF merging of variants',
      },
    ],
    optionalNodes: [
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'LLM-based relevance scoring',
      },
      {
        id: 'llm',
        name: 'Generative Answer',
        description: 'Generate comprehensive answer',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'augmented',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },

  {
    id: 'advanced-rag',
    name: 'Advanced RAG Conversation Agent',
    description: 'Multi-query enhancement with optional reranking & LLM generation',
    icon: '⚙️',
    type: 'rag',
    requiredNodes: [
      {
        id: 'config',
        name: 'Conversation Settings',
        description: 'Name & description',
      },
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'Multi-Query strategy',
      },
      {
        id: 'retrieval',
        name: 'Document Retrieval',
        description: 'Vector search with RRF',
      },
    ],
    optionalNodes: [
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'LLM-based relevance scoring',
      },
      {
        id: 'llm',
        name: 'Generative Answer',
        description: 'Generate answers with LLM',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'multi_query',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },

  {
    id: 'decomposition-rag',
    name: 'Decomposition Conversation Agent Pipeline',
    description: 'Break complex queries into sub-questions for better retrieval',
    icon: '🧩',
    type: 'rag',
    requiredNodes: [
      {
        id: 'config',
        name: 'Conversation Settings',
        description: 'Name & description',
      },
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'Decomposition strategy',
      },
      {
        id: 'retrieval',
        name: 'Document Retrieval',
        description: 'Parallel retrieval for sub-queries',
      },
    ],
    optionalNodes: [
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'Rank by relevance',
      },
      {
        id: 'llm',
        name: 'Generative Answer',
        description: 'Synthesize sub-answers',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'decomposition',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },

  {
    id: 'hyde-rag',
    name: 'HyDE Conversation Agent Pipeline',
    description: 'Generate hypothetical answers to guide document retrieval',
    icon: '🔮',
    type: 'rag',
    requiredNodes: [
      {
        id: 'config',
        name: 'Conversation Settings',
        description: 'Name & description',
      },
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'HyDE strategy',
      },
      {
        id: 'retrieval',
        name: 'Document Retrieval',
        description: 'Search similar to hypothetical answers',
      },
    ],
    optionalNodes: [
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'Filter by relevance',
      },
      {
        id: 'llm',
        name: 'Generative Answer',
        description: 'Generate final answer',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'hyde',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },

  {
    id: 'supervisor-agent',
    name: 'Supervisor Agent (Multi-Task Orchestration)',
    description: 'Intelligent agent orchestrator for handling complex multi-step tasks with knowledge assistant capabilities',
    icon: '🤖',
    type: 'supervisor',
    requiredNodes: [
      {
        id: 'config',
        name: 'Agent Settings',
        description: 'Name, description & agent mode',
      },
      {
        id: 'assistant',
        name: 'Assistant Configuration',
        description: 'Enable knowledge assistant & system prompts',
      },
      {
        id: 'supervisor',
        name: 'Supervisor Orchestrator',
        description: 'Multi-agent task orchestration',
      },
    ],
    optionalNodes: [
      {
        id: 'enhancement',
        name: 'Query Enhancement',
        description: 'Optional query transformation',
      },
      {
        id: 'retrieval',
        name: 'Knowledge Retrieval',
        description: 'Optional knowledge base search',
      },
      {
        id: 'reranking',
        name: 'Document Reranking',
        description: 'Optional result ranking',
      },
    ],
    defaultConfig: {
      selectedStrategy: 'native',
      enableReranking: false,
      enableLLMGeneration: true,
    },
  },
];
