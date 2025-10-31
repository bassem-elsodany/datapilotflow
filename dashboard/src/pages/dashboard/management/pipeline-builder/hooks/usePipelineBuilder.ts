import { useState, useCallback } from 'react';
import {
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
} from 'reactflow';
import { v4 as uuidv4 } from 'uuid';
import { validateConnection, validatePipeline, getValidTargets, getValidSources } from '../utils/pipelineRules';

export interface PipelineNodeData {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  description?: string;
  [key: string]: any;
}

export function usePipelineBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState<PipelineNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node<PipelineNodeData> | null>(null);

  // Disable manual connections - we only use automatic connections based on pipeline rules
  const onConnect = useCallback(() => {
    // Manual connections are disabled - all connections are automatic based on pipeline rules
    console.log('Manual connections are disabled. Connections are automatic based on pipeline rules.');
  }, []);

  const deleteNode = useCallback((id: string) => {
    console.log('Hook: Deleting node with id:', id);
    setNodes((nds) => {
      const filtered = nds.filter((node) => node.id !== id);
      console.log('Hook: Nodes before deletion:', nds.length, 'after:', filtered.length);
      return filtered;
    });
    setEdges((eds) => eds.filter((edge) => edge.source !== id && edge.target !== id));
    if (selectedNode?.id === id) {
      setSelectedNode(null);
    }
  }, [setNodes, setEdges, selectedNode]);

  // Auto-connect nodes based on pipeline rules
  const autoConnectNode = useCallback((newNode: Node<PipelineNodeData>, allNodes: Node<PipelineNodeData>[]) => {
    const nodeType = newNode.data.type;

    // Find potential connections based on pipeline rules
    const validTargets = getValidTargets(nodeType);
    const validSources = getValidSources(nodeType);

    const newEdges: Edge[] = [];

    // Find the MOST RECENT relevant node to connect to (not ALL nodes)
    // This prevents creating multiple connections to every valid node

    // Sort nodes by position (rightmost = most recent in linear flow)
    const sortedNodes = [...allNodes].sort((a, b) => b.position.x - a.position.x);

    // Try to find ONE valid target (downstream connection: newNode -> target)
    const targetNode = sortedNodes.find(node =>
      node.id !== newNode.id && validTargets.includes(node.data.type)
    );

    if (targetNode) {
      newEdges.push({
        id: `edge-${newNode.id}-${targetNode.id}`,
        source: newNode.id,
        sourceHandle: 'source',
        target: targetNode.id,
        targetHandle: 'target',
        type: 'arrow',
        animated: true,
        style: { stroke: '#228be6', strokeWidth: 2 }
      });
      console.log(`Auto-connected: ${nodeType} -> ${targetNode.data.type}`);
    }

    // Try to find ONE valid source (upstream connection: source -> newNode)
    const sourceNode = sortedNodes.find(node =>
      node.id !== newNode.id && validSources.includes(node.data.type)
    );

    if (sourceNode) {
      newEdges.push({
        id: `edge-${sourceNode.id}-${newNode.id}`,
        source: sourceNode.id,
        sourceHandle: 'source',
        target: newNode.id,
        targetHandle: 'target',
        type: 'arrow',
        animated: true,
        style: { stroke: '#228be6', strokeWidth: 2 }
      });
      console.log(`Auto-connected: ${sourceNode.data.type} -> ${nodeType}`);
    }

    // Add new edges
    if (newEdges.length > 0) {
      setEdges((eds) => [...eds, ...newEdges]);
    }
  }, [setEdges]);

  const addNode = useCallback((type: string, position: { x: number; y: number }) => {
    setNodes((currentNodes) => {
      // Only check for duplicate data sources if we're adding a data source
      const isDataSource = ['website', 'multiple_pages', 'single_page', 'local_files', 'confluence'].includes(type);
      if (isDataSource) {
        const existingDataSource = currentNodes.find(node =>
          node.data.type === 'website' ||
          node.data.type === 'multiple_pages' ||
          node.data.type === 'single_page' ||
          node.data.type === 'local_files' ||
          node.data.type === 'confluence'
        );
        if (existingDataSource) {
          console.log(`A data source node already exists on canvas`);
          return currentNodes; // Don't add multiple data sources
        }
      }
    
      const nodeId = uuidv4();
      
      // Smart positioning: if canvas is empty, use center; otherwise, position relative to existing nodes
      let finalPosition = position;
      if (currentNodes.length > 0) {
        // Find the rightmost node and position new node to its right
        const rightmostNode = currentNodes.reduce((rightmost, node) => 
          node.position.x > rightmost.position.x ? node : rightmost
        );
        finalPosition = {
          x: rightmostNode.position.x + 200,
          y: rightmostNode.position.y
        };
      }
      
      // Handle different data source types
      let nodeName = `${type} Node`;
      let nodeDescription = `A ${type} processing node.`;
      let defaultConfig = {};
      
      if (type === 'website') {
        nodeName = 'Website Crawling';
        nodeDescription = 'Crawl and scrape content from websites';
        defaultConfig = {
          scraping_mode: 'website',
          url: '',
          allowed_subdomains: [],
          blocked_subdomains: [],
          url_patterns: [],
          crawl_depth: 4,
          css_selector: 'main > article',
          css_selector_parts: [
            { type: 'main', selector: '' },
            { type: 'article', selector: '' }
          ],
          content_filter_threshold: 0.6,
        };
      } else if (type === 'multiple_pages') {
        nodeName = 'Links File';
        nodeDescription = 'Upload and process files containing multiple URLs';
        defaultConfig = {
          scraping_mode: 'multiple_pages',
          url_source: { file_name: undefined, urls: [] },
          allowed_subdomains: [],
          blocked_subdomains: [],
          url_patterns: [],
          crawl_depth: 4,
          css_selector: 'main > article',
          css_selector_parts: [
            { type: 'main', selector: '' },
            { type: 'article', selector: '' }
          ],
          content_filter_threshold: 0.6,
        };
      } else if (type === 'single_page') {
        nodeName = 'Single Page';
        nodeDescription = 'Crawl and scrape content from a single page';
        defaultConfig = {
          scraping_mode: 'single_page',
          url: '',
          allowed_subdomains: [],
          blocked_subdomains: [],
          url_patterns: [],
          crawl_depth: 1,
          css_selector: 'main > article',
          css_selector_parts: [
            { type: 'main', selector: '' },
            { type: 'article', selector: '' }
          ],
          content_filter_threshold: 0.6,
        };
      } else if (type === 'local_files') {
        nodeName = 'Local Files';
        nodeDescription = 'Upload and process local files (PDF, Markdown, HTML, etc.)';
        defaultConfig = {
          scraping_mode: 'markdown_files',
          local_files: [],
          file_types: ['html', 'markdown', 'pdf', 'docx', 'txt'],
          output_format: 'markdown',
        };
      } else if (type === 'textSplitter') {
        nodeName = 'Document Splitter';
        nodeDescription = 'Split documents into chunks for processing';
        defaultConfig = {
          chunk_size: 1000,
          chunk_overlap: 200,
          batch_size: 100,
        };
      } else if (type === 'confluence') {
        nodeName = 'Confluence';
        nodeDescription = 'Crawl and scrape content from Confluence spaces';
        defaultConfig = {
          scraping_mode: 'confluence',
          url: '',
          allowed_subdomains: [],
          blocked_subdomains: [],
          url_patterns: [],
          crawl_depth: 4,
          css_selector: 'main > article',
          css_selector_parts: [
            { type: 'main', selector: '' },
            { type: 'article', selector: '' }
          ],
          content_filter_threshold: 0.6,
        };
      }
      
      const newNode: Node<PipelineNodeData> = {
        id: nodeId,
        type: 'pipelineNode',
        position: finalPosition,
        data: { 
          id: nodeId,
          name: nodeName,
          type,
          status: 'pending',
          description: nodeDescription,
          onDelete: deleteNode, // Pass delete handler through data
          ...defaultConfig
        },
      };
      
      const updatedNodes = currentNodes.concat(newNode);
      
      // Auto-connect based on pipeline rules
      autoConnectNode(newNode, updatedNodes);
      
      return updatedNodes;
    });
  }, [setNodes, deleteNode, setEdges]);

  const updateNode = useCallback((id: string, data: Partial<PipelineNodeData>) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, ...data } } : node
      )
    );
    setSelectedNode((prev) => 
      prev && prev.id === id ? { ...prev, data: { ...prev.data, ...data } } : prev
    );
  }, [setNodes]);

  const handleNodeSelect = useCallback((node: Node | null) => {
    setSelectedNode(node as Node<PipelineNodeData> | null);
  }, []);

  const clearCanvas = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
  }, [setNodes, setEdges]);

  const savePipeline = useCallback(() => {
    const pipeline = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type
      }))
    };
    console.log('Saving pipeline:', pipeline);
    return pipeline;
  }, [nodes, edges]);

  const loadPipeline = useCallback((pipeline: any) => {
    if (pipeline.nodes && pipeline.edges) {
      setNodes(pipeline.nodes);
      setEdges(pipeline.edges);
    }
  }, [setNodes, setEdges]);

  const validateCurrentPipeline = useCallback(() => {
    return validatePipeline(nodes, edges);
  }, [nodes, edges]);

  return {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    updateNode,
    deleteNode,
    selectedNode,
    setSelectedNode,
    handleNodeSelect,
    clearCanvas,
    savePipeline,
    loadPipeline,
    validateCurrentPipeline,
  };
}