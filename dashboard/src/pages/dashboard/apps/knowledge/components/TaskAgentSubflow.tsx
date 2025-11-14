/**
 * Task Agent Subflow Component
 *
 * Represents the expandable Task Agent pipeline within Task Engine node.
 * Contains nested nodes: System Prompts → Task Execution
 */

import { Node, Edge } from 'reactflow';

export interface TaskAgentSubflowConfig {
  enableKnowledgeAssistant: boolean;
  selectedSystemPromptId?: string;
  selectedTools?: string[]; // Array of tool IDs
  tool_instructions?: string; // Tool orchestration instructions
}

/**
 * Generate Task Agent subflow nodes (children of Task Engine)
 * Nodes are positioned tightly together in a group
 */
export function generateTaskAgentSubflowNodes(parentId: string, baseX: number, baseY: number, config: TaskAgentSubflowConfig): Node[] {
  const nodes: Node[] = [];
  const nodeSpacing = 90; // Tighter spacing for grouped layout

  // Sub-node 1: Tools
  // Configured if: selectedTools array has items
  nodes.push({
    id: `${parentId}-prompts`,
    type: 'conversationNode',
    position: { x: baseX, y: baseY },
    data: {
      id: `${parentId}-prompts`,
      name: 'Tools Configuration',
      type: 'assistant',
      description: 'Select enabled tools',
      configured: !!(config.selectedTools && config.selectedTools.length > 0),
    },
  });

  // Sub-node 2: Task Execution
  nodes.push({
    id: `${parentId}-execution`,
    type: 'conversationNode',
    position: { x: baseX + nodeSpacing, y: baseY },
    data: {
      id: `${parentId}-execution`,
      name: 'Task Execution',
      type: 'taskEngine',
      description: 'Execute tasks & tools',
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
      markerEnd: { type: 'arrowclosed', color: '#51cf66', scale: 0.5 },
    },
  ];
}
