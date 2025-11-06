/**
 * RAG Subflow Component
 *
 * Represents a collapsible RAG pipeline subflow within the Knowledge Retrieval node.
 * Contains nested nodes: Enhancement → Search → Rerank → Generate
 */

import { Node, Edge } from 'reactflow';

export interface RAGSubflowConfig {
  // Enhancement (Query Strategy)
  selectedStrategy: string;

  // Vector Search (Retrieval)
  collectionName: string;
  topK: number;

  // Reranking
  enableReranking: boolean;
  selectedRerankerId?: string;
  selectedRerankerModel?: string;
  relevanceThreshold?: number;

  // Generation
  enableLLMGeneration: boolean;
  selectedProviderId?: string;
  selectedModel?: string;
}

/**
 * Generate RAG subflow nodes
 * These are child nodes that appear when Knowledge Retrieval is expanded
 */
export function generateRAGSubflowNodes(parentId: string, baseX: number, baseY: number, config: RAGSubflowConfig): Node[] {
  const nodes: Node[] = [];
  const nodeSpacing = 120;

  // Sub-node 1: Query Enhancement
  nodes.push({
    id: `${parentId}-enhancement`,
    type: 'conversationNode',
    position: { x: baseX, y: baseY },
    data: {
      id: `${parentId}-enhancement`,
      name: 'Query Strategy',
      type: 'enhancement',
      description: 'Transform query for better retrieval',
      configured: !!config.selectedStrategy,
      parentId: parentId, // Link to parent node
    },
    parent: parentId,
    extent: 'parent' as const,
  });

  // Sub-node 2: Vector Search
  nodes.push({
    id: `${parentId}-search`,
    type: 'conversationNode',
    position: { x: baseX + nodeSpacing, y: baseY },
    data: {
      id: `${parentId}-search`,
      name: 'Vector Search',
      type: 'retrieval',
      description: 'Search knowledge base',
      configured: !!config.collectionName && config.topK > 0,
      parentId: parentId,
    },
    parent: parentId,
    extent: 'parent' as const,
  });

  // Sub-node 3: Reranking (optional)
  if (config.enableReranking) {
    nodes.push({
      id: `${parentId}-rerank`,
      type: 'conversationNode',
      position: { x: baseX + nodeSpacing * 2, y: baseY },
      data: {
        id: `${parentId}-rerank`,
        name: 'Rerank Results',
        type: 'reranking',
        description: 'Filter by relevance',
        configured: !!config.selectedRerankerId && !!config.selectedRerankerModel,
        parentId: parentId,
      },
      parent: parentId,
      extent: 'parent' as const,
    });
  }

  // Sub-node 4: Generate Answer (optional)
  if (config.enableLLMGeneration) {
    const xPos = config.enableReranking ? baseX + nodeSpacing * 3 : baseX + nodeSpacing * 2;
    nodes.push({
      id: `${parentId}-generate`,
      type: 'conversationNode',
      position: { x: xPos, y: baseY },
      data: {
        id: `${parentId}-generate`,
        name: 'Generate Answer',
        type: 'llm',
        description: 'Generate response',
        configured: !!config.selectedProviderId && !!config.selectedModel,
        parentId: parentId,
      },
      parent: parentId,
      extent: 'parent' as const,
    });
  }

  return nodes;
}

/**
 * Generate RAG subflow edges (connections between sub-nodes)
 */
export function generateRAGSubflowEdges(parentId: string, config: RAGSubflowConfig): Edge[] {
  const edges: Edge[] = [];

  // Enhancement → Search
  edges.push({
    id: `${parentId}-enhancement-to-search`,
    source: `${parentId}-enhancement`,
    target: `${parentId}-search`,
    animated: true,
  });

  // Search → Rerank or Generate
  const nextNodeId = config.enableReranking ? `${parentId}-rerank` : (config.enableLLMGeneration ? `${parentId}-generate` : undefined);
  if (nextNodeId) {
    edges.push({
      id: `${parentId}-search-to-next`,
      source: `${parentId}-search`,
      target: nextNodeId,
      animated: true,
    });
  }

  // Rerank → Generate (if both enabled)
  if (config.enableReranking && config.enableLLMGeneration) {
    edges.push({
      id: `${parentId}-rerank-to-generate`,
      source: `${parentId}-rerank`,
      target: `${parentId}-generate`,
      animated: true,
    });
  }

  return edges;
}
