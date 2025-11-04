/**
 * RAG Pipeline Templates
 *
 * Pre-built pipeline templates for common RAG scenarios.
 * Users can select a template and customize it by removing optional nodes.
 */

import { Node, Edge } from 'reactflow';

export interface RagTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  requiredNodes: Array<{
    id: string;
    type: string;
    label: string;
    description: string;
  }>;
  optionalNodes: Array<{
    id: string;
    type: string;
    label: string;
    description: string;
  }>;
  defaultNodes: Node[];
  defaultEdges: Edge[];
}

export const RAG_TEMPLATES: RagTemplate[] = [
  {
    id: 'basic-rag',
    name: 'Basic RAG',
    description: 'Simple pipeline: Website → Markdown → Splitter → Embeddings → Vector DB',
    icon: '📦',
    requiredNodes: [
      { id: 'website', type: 'website', label: 'Website Crawling', description: 'Crawl content from websites' },
      { id: 'markdown', type: 'markdownGenerator', label: 'Markdown Generator', description: 'Convert to markdown format' },
      { id: 'splitter', type: 'textSplitter', label: 'Document Splitter', description: 'Split documents into chunks' },
      { id: 'embeddings', type: 'embeddingGenerator', label: 'Embedding Generator', description: 'Generate vector embeddings' },
      { id: 'vectordb', type: 'vectorDatabase', label: 'Vector Database', description: 'Store embeddings in vector DB' },
    ],
    optionalNodes: [
      { id: 'contentFilter', type: 'contentFilter', label: 'Content Filter', description: 'Filter content by keywords/patterns' },
      { id: 'llmFilter', type: 'llmContentFilter', label: 'LLM Content Filter', description: 'Use LLM to intelligently filter content' },
    ],
    defaultNodes: [
      {
        id: 'website-1',
        type: 'pipelineNode',
        position: { x: 0, y: 0 },
        data: { id: 'website-1', name: 'Website', type: 'website', configured: false },
      },
      {
        id: 'markdown-1',
        type: 'pipelineNode',
        position: { x: 200, y: 0 },
        data: { id: 'markdown-1', name: 'Markdown Generator', type: 'markdownGenerator', configured: false },
      },
      {
        id: 'splitter-1',
        type: 'pipelineNode',
        position: { x: 400, y: 0 },
        data: { id: 'splitter-1', name: 'Document Splitter', type: 'textSplitter', configured: false },
      },
      {
        id: 'embeddings-1',
        type: 'pipelineNode',
        position: { x: 600, y: 0 },
        data: { id: 'embeddings-1', name: 'Embeddings', type: 'embeddingGenerator', configured: false },
      },
      {
        id: 'vectordb-1',
        type: 'pipelineNode',
        position: { x: 800, y: 0 },
        data: { id: 'vectordb-1', name: 'Vector DB', type: 'vectorDatabase', configured: false },
      },
    ],
    defaultEdges: [
      { id: 'edge-website-markdown', source: 'website-1', target: 'markdown-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-markdown-splitter', source: 'markdown-1', target: 'splitter-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-splitter-embeddings', source: 'splitter-1', target: 'embeddings-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-embeddings-vectordb', source: 'embeddings-1', target: 'vectordb-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
    ],
  },

  {
    id: 'advanced-rag',
    name: 'Advanced RAG with Content Filter',
    description: 'Website → Markdown → Content Filter → Splitter → Embeddings → Vector DB',
    icon: '⚙️',
    requiredNodes: [
      { id: 'website', type: 'website', label: 'Website Crawling', description: 'Crawl content from websites' },
      { id: 'markdown', type: 'markdownGenerator', label: 'Markdown Generator', description: 'Convert to markdown format' },
      { id: 'contentFilter', type: 'contentFilter', label: 'Content Filter', description: 'Filter content by keywords/patterns' },
      { id: 'splitter', type: 'textSplitter', label: 'Document Splitter', description: 'Split documents into chunks' },
      { id: 'embeddings', type: 'embeddingGenerator', label: 'Embedding Generator', description: 'Generate vector embeddings' },
      { id: 'vectordb', type: 'vectorDatabase', label: 'Vector Database', description: 'Store embeddings in vector DB' },
    ],
    optionalNodes: [
      { id: 'llmFilter', type: 'llmContentFilter', label: 'LLM Content Filter', description: 'Use LLM to intelligently filter content' },
      { id: 'domainFilter', type: 'domainFilter', label: 'Domain Filter', description: 'Filter by domain whitelist/blacklist (optional)' },
    ],
    defaultNodes: [
      {
        id: 'website-1',
        type: 'pipelineNode',
        position: { x: 0, y: 0 },
        data: { id: 'website-1', name: 'Website', type: 'website', configured: false },
      },
      {
        id: 'markdown-1',
        type: 'pipelineNode',
        position: { x: 200, y: 0 },
        data: { id: 'markdown-1', name: 'Markdown Generator', type: 'markdownGenerator', configured: false },
      },
      {
        id: 'contentFilter-1',
        type: 'pipelineNode',
        position: { x: 400, y: 0 },
        data: { id: 'contentFilter-1', name: 'Content Filter', type: 'contentFilter', configured: false },
      },
      {
        id: 'splitter-1',
        type: 'pipelineNode',
        position: { x: 600, y: 0 },
        data: { id: 'splitter-1', name: 'Document Splitter', type: 'textSplitter', configured: false },
      },
      {
        id: 'embeddings-1',
        type: 'pipelineNode',
        position: { x: 800, y: 0 },
        data: { id: 'embeddings-1', name: 'Embeddings', type: 'embeddingGenerator', configured: false },
      },
      {
        id: 'vectordb-1',
        type: 'pipelineNode',
        position: { x: 1000, y: 0 },
        data: { id: 'vectordb-1', name: 'Vector DB', type: 'vectorDatabase', configured: false },
      },
    ],
    defaultEdges: [
      { id: 'edge-website-markdown', source: 'website-1', target: 'markdown-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-markdown-filter', source: 'markdown-1', target: 'contentFilter-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-filter-splitter', source: 'contentFilter-1', target: 'splitter-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-splitter-embeddings', source: 'splitter-1', target: 'embeddings-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-embeddings-vectordb', source: 'embeddings-1', target: 'vectordb-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
    ],
  },

  {
    id: 'web-crawler-rag',
    name: 'Web Crawler RAG',
    description: 'Multi-page crawler: Links File → HTML Extractor → Markdown → Splitter → Embeddings → Vector DB',
    icon: '🌐',
    requiredNodes: [
      { id: 'multipage', type: 'multiple_pages', label: 'Links File', description: 'Load URLs from file' },
      { id: 'htmlExtractor', type: 'htmlExtractor', label: 'HTML Extractor', description: 'Extract HTML content' },
      { id: 'splitter', type: 'textSplitter', label: 'Document Splitter', description: 'Split documents into chunks' },
      { id: 'embeddings', type: 'embeddingGenerator', label: 'Embedding Generator', description: 'Generate vector embeddings' },
      { id: 'vectordb', type: 'vectorDatabase', label: 'Vector Database', description: 'Store embeddings in vector DB' },
    ],
    optionalNodes: [
      { id: 'llmFilter', type: 'llmContentFilter', label: 'LLM Content Filter', description: 'Use LLM to intelligently filter content' },
      { id: 'llmMarkdown', type: 'llmMarkdownGenerator', label: 'LLM Markdown Generator', description: 'Use LLM for better markdown conversion' },
      { id: 'domainFilter', type: 'domainFilter', label: 'Domain Filter', description: 'Filter by domain whitelist/blacklist' },
    ],
    defaultNodes: [
      {
        id: 'multipage-1',
        type: 'pipelineNode',
        position: { x: 0, y: 0 },
        data: { id: 'multipage-1', name: 'Links File', type: 'multiple_pages', configured: false },
      },
      {
        id: 'htmlExtractor-1',
        type: 'pipelineNode',
        position: { x: 200, y: 0 },
        data: { id: 'htmlExtractor-1', name: 'HTML Extractor', type: 'htmlExtractor', configured: false },
      },
      {
        id: 'splitter-1',
        type: 'pipelineNode',
        position: { x: 400, y: 0 },
        data: { id: 'splitter-1', name: 'Document Splitter', type: 'textSplitter', configured: false },
      },
      {
        id: 'embeddings-1',
        type: 'pipelineNode',
        position: { x: 600, y: 0 },
        data: { id: 'embeddings-1', name: 'Embeddings', type: 'embeddingGenerator', configured: false },
      },
      {
        id: 'vectordb-1',
        type: 'pipelineNode',
        position: { x: 800, y: 0 },
        data: { id: 'vectordb-1', name: 'Vector DB', type: 'vectorDatabase', configured: false },
      },
    ],
    defaultEdges: [
      { id: 'edge-multipage-html', source: 'multipage-1', target: 'htmlExtractor-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-html-splitter', source: 'htmlExtractor-1', target: 'splitter-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-splitter-embeddings', source: 'splitter-1', target: 'embeddings-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-embeddings-vectordb', source: 'embeddings-1', target: 'vectordb-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
    ],
  },

  {
    id: 'local-files-rag',
    name: 'Local Files RAG',
    description: 'Process local documents: Files → Markdown → Splitter → Embeddings → Vector DB',
    icon: '📄',
    requiredNodes: [
      { id: 'localfiles', type: 'local_files', label: 'Local Files', description: 'Upload local documents' },
      { id: 'markdown', type: 'markdownGenerator', label: 'Markdown Generator', description: 'Convert to markdown format' },
      { id: 'splitter', type: 'textSplitter', label: 'Document Splitter', description: 'Split documents into chunks' },
      { id: 'embeddings', type: 'embeddingGenerator', label: 'Embedding Generator', description: 'Generate vector embeddings' },
      { id: 'vectordb', type: 'vectorDatabase', label: 'Vector Database', description: 'Store embeddings in vector DB' },
    ],
    optionalNodes: [
      { id: 'contentFilter', type: 'contentFilter', label: 'Content Filter', description: 'Filter content by keywords/patterns' },
    ],
    defaultNodes: [
      {
        id: 'localfiles-1',
        type: 'pipelineNode',
        position: { x: 0, y: 0 },
        data: { id: 'localfiles-1', name: 'Local Files', type: 'local_files', configured: false },
      },
      {
        id: 'markdown-1',
        type: 'pipelineNode',
        position: { x: 200, y: 0 },
        data: { id: 'markdown-1', name: 'Markdown Generator', type: 'markdownGenerator', configured: false },
      },
      {
        id: 'splitter-1',
        type: 'pipelineNode',
        position: { x: 400, y: 0 },
        data: { id: 'splitter-1', name: 'Document Splitter', type: 'textSplitter', configured: false },
      },
      {
        id: 'embeddings-1',
        type: 'pipelineNode',
        position: { x: 600, y: 0 },
        data: { id: 'embeddings-1', name: 'Embeddings', type: 'embeddingGenerator', configured: false },
      },
      {
        id: 'vectordb-1',
        type: 'pipelineNode',
        position: { x: 800, y: 0 },
        data: { id: 'vectordb-1', name: 'Vector DB', type: 'vectorDatabase', configured: false },
      },
    ],
    defaultEdges: [
      { id: 'edge-localfiles-markdown', source: 'localfiles-1', target: 'markdown-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-markdown-splitter', source: 'markdown-1', target: 'splitter-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-splitter-embeddings', source: 'splitter-1', target: 'embeddings-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
      { id: 'edge-embeddings-vectordb', source: 'embeddings-1', target: 'vectordb-1', type: 'default', animated: true, markerEnd: { type: 'arrowclosed' }, style: { stroke: '#228be6', strokeWidth: 2 } },
    ],
  },
];
