/**
 * Task Agent Subflow Component
 *
 * Represents the expandable Task Agent pipeline within Task Engine node.
 * Contains nested nodes: System Prompts → Task Execution
 */

import { Node, Edge } from 'reactflow';

export interface TaskAgentSubflowConfig {
  enableKnowledgeAssistant: boolean;
}

/**
 * Generate Task Agent subflow nodes (children of Task Engine)
 * Nodes are positioned tightly together in a group
 */
export function generateTaskAgentSubflowNodes(parentId: string, baseX: number, baseY: number, config: TaskAgentSubflowConfig): Node[] {
  const nodes: Node[] = [];
  const nodeSpacing = 90; // Tighter spacing for grouped layout

  // Sub-node 1: System Prompts
  nodes.push({
    id: `${parentId}-prompts`,
    type: 'conversationNode',
    position: { x: baseX, y: baseY },
    data: {
      id: `${parentId}-prompts`,
      name: 'System Prompts',
      type: 'assistant',
      description: 'Task instructions',
      configured: true,
    },
  });

  // Sub-node 2: Task Execution
  nodes.push({
    id: `${parentId}-execution`,
    type: 'conversationNode',
    position: { x: baseX + nodeSpacing, y: baseY },
    data: {
      id: `${parentId}-execution`,
      name: 'Execution',
      type: 'taskEngine',
      description: 'Multi-task orchestration',
      configured: config.enableKnowledgeAssistant,
    },
  });

  return nodes;
}

/**
 * Generate Task Agent subflow edges
 */
export function generateTaskAgentSubflowEdges(parentId: string): Edge[] {
  return [
    {
      id: `${parentId}-e-prompts-to-execution`,
      source: `${parentId}-prompts`,
      target: `${parentId}-execution`,
      animated: true,
      markerEnd: { type: 'arrow', color: '#228be6' },
    },
  ];
}
