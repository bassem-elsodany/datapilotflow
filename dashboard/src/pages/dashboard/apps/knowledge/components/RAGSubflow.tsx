/**
 * RAG Subflow Component
 *
 * Represents the expandable RAG Agent pipeline within Knowledge Retrieval node.
 * Contains nested nodes: Enhancement → Search → Rerank → Generate
 */

import { Node, Edge } from 'reactflow';

export interface RAGSubflowConfig {
  selectedStrategy: string;
  collectionName: string;
  topK: number;
  enableReranking: boolean;
  selectedRerankerId?: string;
  selectedRerankerModel?: string;
  enableLLMGeneration: boolean;
  selectedProviderId?: string;
  selectedModel?: string;
}

/**
 * Generate RAG subflow nodes (children of Knowledge Retrieval)
 * Nodes are positioned tightly together in a group
 */
export function generateRAGSubflowNodes(parentId: string, baseX: number, baseY: number, config: RAGSubflowConfig): Node[] {
  const nodes: Node[] = [];
  const nodeSpacing = 90; // Tighter spacing for grouped layout

  // Sub-node 1: Query Enhancement
  // Configured if: strategy is set AND (if non-native, LLM provider and model are set)
  let enhancementConfigured = !!config.selectedStrategy;
  if (enhancementConfigured && config.selectedStrategy !== 'native') {
    enhancementConfigured = !!config.selectedProviderId && !!config.selectedModel;
  }

  nodes.push({
    id: `${parentId}-enhancement`,
    type: 'conversationNode',
    position: { x: baseX, y: baseY },
    data: {
      id: `${parentId}-enhancement`,
      name: 'Enhancement',
      type: 'enhancement',
      description: 'Query strategy',
      configured: enhancementConfigured,
    },
  });

  // Sub-node 2: Vector Search
  // Configured if: collection name AND topK are set
  nodes.push({
    id: `${parentId}-search`,
    type: 'conversationNode',
    position: { x: baseX + nodeSpacing, y: baseY },
    data: {
      id: `${parentId}-search`,
      name: 'Search',
      type: 'retrieval',
      description: 'Vector search',
      configured: !!config.collectionName && !!config.topK,
    },
  });

  // Sub-node 3: Reranking (optional)
  if (config.enableReranking) {
    nodes.push({
      id: `${parentId}-rerank`,
      type: 'conversationNode',
      position: { x: baseX + nodeSpacing * 2, y: baseY },
      data: {
        id: `${parentId}-rerank`,
        name: 'Rerank',
        type: 'reranking',
        description: 'Filter results',
        configured: !!config.selectedRerankerId && !!config.selectedRerankerModel,
      },
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
        name: 'Generate',
        type: 'llm',
        description: 'Answer generation',
        configured: !!config.selectedProviderId && !!config.selectedModel,
      },
    });
  }

  return nodes;
}

/**
 * Generate RAG subflow edges
 */
export function generateRAGSubflowEdges(parentId: string, config: RAGSubflowConfig): Edge[] {
  const edges: Edge[] = [];

  // Enhancement → Search
  edges.push({
    id: `${parentId}-e-enhancement-to-search`,
    source: `${parentId}-enhancement`,
    target: `${parentId}-search`,
    animated: true,
    markerEnd: { type: 'arrowclosed', color: '#51cf66', scale: 0.5 },
  });

  // Search → Rerank or Generate
  const nextNodeId = config.enableReranking ? `${parentId}-rerank` : (config.enableLLMGeneration ? `${parentId}-generate` : undefined);
  if (nextNodeId) {
    edges.push({
      id: `${parentId}-e-search-to-next`,
      source: `${parentId}-search`,
      target: nextNodeId,
      animated: true,
      markerEnd: { type: 'arrowclosed', color: '#51cf66', scale: 0.5 },
    });
  }

  // Rerank → Generate
  if (config.enableReranking && config.enableLLMGeneration) {
    edges.push({
      id: `${parentId}-e-rerank-to-generate`,
      source: `${parentId}-rerank`,
      target: `${parentId}-generate`,
      animated: true,
      markerEnd: { type: 'arrowclosed', color: '#51cf66', scale: 0.5 },
    });
  }

  return edges;
}
