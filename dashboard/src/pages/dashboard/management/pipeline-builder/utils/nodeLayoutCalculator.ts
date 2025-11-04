/**
 * Node Layout Calculator
 *
 * Calculates optimal node positions for multi-line rendering.
 * Renders nodes in a "train" layout with max 4 nodes per line.
 */

import { Node } from 'reactflow';

export interface NodeLayoutConfig {
  nodesPerLine: number;
  horizontalSpacing: number;
  verticalSpacing: number;
  startX: number;
  startY: number;
}

const DEFAULT_CONFIG: NodeLayoutConfig = {
  nodesPerLine: 4,
  horizontalSpacing: 250,
  verticalSpacing: 200,
  startX: 50,
  startY: 50,
};

/**
 * Calculate positions for nodes in a multi-line grid layout
 * Arranges nodes in horizontal lines with max 4 nodes per line
 *
 * Example with 6 nodes:
 * Line 1: [Node1] [Node2] [Node3] [Node4]
 * Line 2: [Node5] [Node6]
 */
export function calculateNodePositions(
  nodes: Node[],
  config: Partial<NodeLayoutConfig> = {}
): Node[] {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  const { nodesPerLine, horizontalSpacing, verticalSpacing, startX, startY } = finalConfig;

  return nodes.map((node, index) => {
    // Calculate which line this node is on (0-indexed)
    const lineNumber = Math.floor(index / nodesPerLine);
    // Calculate position within the line (0-indexed)
    const positionInLine = index % nodesPerLine;

    // Calculate X and Y coordinates
    const x = startX + positionInLine * horizontalSpacing;
    const y = startY + lineNumber * verticalSpacing;

    return {
      ...node,
      position: { x, y },
    };
  });
}

/**
 * Reposition nodes after filtering (e.g., when optional nodes are deselected)
 * This is useful when users deselect optional nodes and need to reorganize
 */
export function repositionNodes(
  nodes: Node[],
  config: Partial<NodeLayoutConfig> = {}
): Node[] {
  return calculateNodePositions(nodes, config);
}

/**
 * Get layout statistics for debugging/display
 */
export function getLayoutStats(nodes: Node[], nodesPerLine: number = DEFAULT_CONFIG.nodesPerLine) {
  const totalNodes = nodes.length;
  const totalLines = Math.ceil(totalNodes / nodesPerLine);
  const lastLineNodeCount = ((totalNodes - 1) % nodesPerLine) + 1;

  return {
    totalNodes,
    totalLines,
    nodesPerLine,
    lastLineNodeCount,
    firstLineNodes: Math.min(totalNodes, nodesPerLine),
  };
}

/**
 * Calculate staircase layout with 2 nodes per row stepping down vertically
 * Creates a vertical cascading pattern like stairs
 *
 * Example with 6 nodes:
 * [Node1] [Node2]
 * [Node3] [Node4]
 *         [Node5] [Node6]
 */
export function calculateStaircaseLayout(
  nodes: Node[],
  config: Partial<NodeLayoutConfig> = {}
): Node[] {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  const { horizontalSpacing, verticalSpacing, startX, startY } = finalConfig;
  const nodesPerRow = 2; // Fixed 2 nodes per row for staircase

  return nodes.map((node, index) => {
    // Calculate which row this node is on (0-indexed)
    const rowNumber = Math.floor(index / nodesPerRow);
    // Calculate position within the row (0 or 1)
    const positionInRow = index % nodesPerRow;

    // Calculate X coordinate - nodes in same row stay at same X plus offset per position
    // First node of each pair moves right, second node appears below
    const x = startX + (rowNumber * horizontalSpacing);

    // Calculate Y coordinate - each position in row gets vertical spacing
    const y = startY + rowNumber * verticalSpacing + positionInRow * verticalSpacing;

    return {
      ...node,
      position: { x, y },
    };
  });
}

/**
 * Create optimized layout for specific pipeline types
 * Can be extended to create custom layouts for different pipeline archetypes
 */
export function createOptimizedLayout(
  nodes: Node[],
  pipelineType?: 'basic' | 'advanced' | 'crawler' | 'custom' | 'staircase'
): Node[] {
  const configs: Record<string, Partial<NodeLayoutConfig>> = {
    basic: {
      nodesPerLine: 5,
      horizontalSpacing: 220,
      verticalSpacing: 150,
    },
    advanced: {
      nodesPerLine: 4,
      horizontalSpacing: 250,
      verticalSpacing: 180,
    },
    crawler: {
      nodesPerLine: 5,
      horizontalSpacing: 220,
      verticalSpacing: 180,
    },
    staircase: {
      nodesPerLine: 2,
      horizontalSpacing: 250,
      verticalSpacing: 200,
    },
    custom: {
      nodesPerLine: 4,
      horizontalSpacing: 250,
      verticalSpacing: 180,
    },
  };

  // Use staircase layout for staircase type
  if (pipelineType === 'staircase') {
    const config = configs.staircase || configs.custom;
    return calculateStaircaseLayout(nodes, config);
  }

  const config = configs[pipelineType || 'custom'] || configs.custom;
  return calculateNodePositions(nodes, config);
}
