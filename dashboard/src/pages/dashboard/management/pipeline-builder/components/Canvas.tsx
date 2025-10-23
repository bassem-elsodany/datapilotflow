/**
 * Pipeline Builder Canvas
 * 
 * Interactive canvas for building visual pipelines with drag-and-drop functionality.
 * Uses React Flow for node-based editing with custom node types.
 */

import React, { useCallback, useMemo, useRef } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlowProvider,
  Node,
  Edge,
  Connection,
  OnNodesChange,
  OnEdgesChange,
  BackgroundVariant,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { PipelineNode } from './PipelineNode';
import { ArrowEdge } from './ArrowEdge';
import { validateConnection, getValidTargets, validatePipeline } from '../utils/pipelineRules';

// Create a stable nodeTypes object outside the component
const nodeTypes = {
  pipelineNode: PipelineNode
};



interface CanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodeSelect: (node: Node | null) => void;
  onNodeUpdate: (id: string, data: any) => void;
  onNodeDelete: (id: string) => void;
  onNodeConfigure: (node: Node) => void;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
}

export function CanvasWrapper({
  nodes,
  edges,
  onNodeSelect,
  onNodeUpdate,
  onNodeDelete,
  onNodeConfigure,
  onNodesChange,
  onEdgesChange,
}: CanvasProps) {
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null);
  
  // Memoize edgeTypes to prevent recreation
  const edgeTypes = useMemo(() => ({
    arrow: ArrowEdge
  }), []);
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    onNodeSelect(node);
  }, [onNodeSelect]);

  const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
    onNodeConfigure(node);
  }, [onNodeConfigure]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance;
  }, []);


  // Handle drag and drop from toolbox
  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;

    // Check if a data source node already exists
    const existingDataSource = nodes.find(node => 
      node.data.type === 'website' || 
      node.data.type === 'multiple_pages' || 
      node.data.type === 'single_page' ||
      node.data.type === 'confluence'
    );
    if (existingDataSource) {
      console.log(`A data source node already exists on canvas`);
      return; // Don't add multiple data sources
    }

    // Get the position where the node was dropped
    const reactFlowBounds = event.currentTarget.getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };

    // Create new node at drop position
    const nodeId = `node-${Date.now()}`;
    const newNode = {
      id: nodeId,
      type: 'pipelineNode',
      position,
      data: {
        id: nodeId,
        name: `${type} Node`,
        type,
        status: 'pending',
        description: `A ${type} processing node.`,
        onDelete: onNodeDelete, // Pass delete handler through data
      },
    };

    // Add the new node
    onNodesChange([{ type: 'add', item: newNode }]);
  }, [onNodesChange, nodes, onNodeDelete]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    // Add visual feedback during drag over
    const target = event.currentTarget as HTMLElement;
    target.style.backgroundColor = '#f0f8ff';
  }, []);

  const onDragLeave = useCallback((event: React.DragEvent) => {
    // Remove visual feedback when drag leaves
    const target = event.currentTarget as HTMLElement;
    target.style.backgroundColor = '';
  }, []);

  // Handle keyboard events for node deletion
  const onKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Delete' || event.key === 'Backspace') {
      // Find selected nodes and delete them
      const selectedNodes = nodes.filter(node => node.selected);
      selectedNodes.forEach(node => onNodeDelete(node.id));
    }
  }, [nodes, onNodeDelete]);


    return (
      <div 
        style={{ width: '100%', height: '100%' }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onKeyDown={onKeyDown}
        tabIndex={0}
      >
      <ReactFlowProvider>
               <ReactFlow
                 nodes={nodes}
                 edges={edges}
                 onNodesChange={onNodesChange}
                 onEdgesChange={onEdgesChange}
                 nodeTypes={nodeTypes}
                 edgeTypes={edgeTypes}
                 onNodeClick={onNodeClick}
                 onNodeDoubleClick={onNodeDoubleClick}
                 onInit={onInit}
                 fitView
               >
          <MiniMap />
          <Controls />
                 <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}