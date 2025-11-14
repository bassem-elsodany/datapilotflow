/**
 * Conversation Canvas Builder
 *
 * Full React Flow canvas for building conversation pipelines
 * Maps to the wizard configuration options
 */

import { useGetActiveModelProviders } from '@/api/resources/model-providers';
import { useGetCollections } from '@/api/resources/vectordb';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { apiUtils } from '@/config';
import { paths } from '@/routes/paths';
import {
  Badge,
  Button,
  Container,
  Group,
  Modal,
  Paper,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconRefresh
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MarkerType,
  MiniMap,
  Node,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ConversationNode } from './ConversationNode';
import { ConversationNodeConfigPanel } from './ConversationNodeConfigPanel';
import { ConversationTemplate } from './conversationTemplates';
import { ConversationTemplateSelector } from './ConversationTemplateSelector';
import { RAGSubflowConfig, generateRAGSubflowEdges, generateRAGSubflowNodes } from './RAGSubflow';
import { TaskAgentSubflowConfig, generateTaskAgentSubflowEdges, generateTaskAgentSubflowNodes } from './TaskAgentSubflow';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Apps', href: paths.dashboard.apps.root },
  { label: 'Knowledge Conversations', href: paths.dashboard.apps.conversationCreate },
  { label: 'Conversation Pipeline' },
];

const nodeTypes = {
  conversationNode: ConversationNode,
};

// Enhancement strategies
const ENHANCEMENT_STRATEGIES = [
  { value: 'native', label: 'Native RAG' },
  { value: 'augmented', label: 'Augmented (Best Coverage)' },
  { value: 'multi_query', label: 'Multi-Query' },
  { value: 'hyde', label: 'HyDE' },
];

interface ConversationConfig {
  conversationName: string;
  conversationDescription: string;
  selectedStrategy: string;
  collectionName: string;
  selectedProviderId: string | null;
  selectedModel: string | null;
  enableReranking: boolean;
  selectedRerankerId: string | null;
  selectedRerankerModel: string | null;
  enableLLMGeneration: boolean;
  enableKnowledgeAssistant: boolean;
  topK: number;
  // Assistant/System Prompt configuration
  selectedSystemPromptId?: string | null;
  selectedSystemPrompt?: any;
  systemPromptTasks?: any[];
  // Template information
  selectedTemplate?: ConversationTemplate;
  // Track which nodes user has configured
  configuredNodes?: {
    enhancement?: boolean;
    retrieval?: boolean;
    reranking?: boolean;
    llm?: boolean;
    assistant?: boolean;
    supervisor?: boolean;
    taskEngine?: boolean;
  };
  // Track expanded subflows for Assistant Agent
  expandedSubflows?: {
    retrieval?: boolean;
    taskEngine?: boolean;
  };
}

function ConversationCanvasContent() {
  const navigate = useNavigate();
  const { data: providers } = useGetActiveModelProviders();
  const { data: collections } = useGetCollections();

  // Template selection state
  const [templateSelected, setTemplateSelected] = useState(false);

  // Basic info modal state
  const [basicInfoModalOpen, setBasicInfoModalOpen] = useState(false);

  // Configuration state
  const [config, setConfig] = useState<ConversationConfig>({
    conversationName: '',
    conversationDescription: '',
    selectedStrategy: 'native',
    collectionName: '', // User MUST select collection
    selectedProviderId: null,
    selectedModel: null,
    enableReranking: false,
    selectedRerankerId: null,
    selectedRerankerModel: null,
    enableLLMGeneration: true,
    enableKnowledgeAssistant: true,
    topK: 5, // Default topK
    configuredNodes: {
      enhancement: false,
      retrieval: false,
      reranking: false,
      llm: false,
    },
    expandedSubflows: {
      retrieval: false,
      taskEngine: false,
    },
  });

  // Debug: Log config changes
  useEffect(() => {
    console.log('[CONFIG STATE CHANGED]:', {
      'configuredNodes': config.configuredNodes,
      'collectionName': config.collectionName,
      'retrieval flag': config.configuredNodes?.retrieval,
    });
  }, [config.configuredNodes, config.collectionName]);

  // Positioning constants for the canvas
  const HORIZONTAL_SPACING = 160; // Compact spacing to fit all nodes without scrolling (max 5 nodes = 30 + 4*160 = 670px)
  const VERTICAL_SPACING = 200;
  const START_X = 30;
  const START_Y = 50;
  const NODES_PER_LINE = 4;

  // Helper function to check if all RAG subflow nodes are configured
  const areRAGSubflowNodesConfigured = (): boolean => {
    // Enhancement is configured if selectedStrategy is set AND
    // if it's non-native (and not custom_variants), LLM provider and model must also be set
    // custom_variants doesn't need LLM since user provides pre-defined variants
    let enhancementConfigured = !!config.selectedStrategy;
    if (enhancementConfigured && config.selectedStrategy !== 'native' && config.selectedStrategy !== 'custom_variants') {
      enhancementConfigured = !!config.selectedProviderId && !!config.selectedModel;
    }

    // Retrieval is configured if collectionName and topK are set
    const retrievalConfigured = !!config.collectionName && !!config.topK;

    // Reranking is configured if enabled and provider/model are set
    const rerangingConfigured = !config.enableReranking || (!!config.selectedRerankerId && !!config.selectedRerankerModel);

    // LLM generation is configured if enabled and provider/model are set
    const llmConfigured = !config.enableLLMGeneration || (!!config.selectedProviderId && !!config.selectedModel);

    return enhancementConfigured && retrievalConfigured && rerangingConfigured && llmConfigured;
  };

  // Helper function to check if all Task Agent subflow nodes are configured
  const areTaskSubflowNodesConfigured = (): boolean => {
    // System Prompts is configured if selectedSystemPromptId is set
    const systemPromptsConfigured = !!config.selectedSystemPromptId;

    // Task Execution is configured if enableKnowledgeAssistant is true
    const taskExecutionConfigured = config.enableKnowledgeAssistant !== false;

    return systemPromptsConfigured && taskExecutionConfigured;
  };

  // Dynamic node generation based on configuration
  // RAG flow: User Query → Query Strategy → Search Documents → Rerank? → Generate Answer/Raw Output
  // Supervisor flow: User Query → Task Analyzer → Supervisor → Tool Execution → Response
  // Settings (conversation name & description) handled in modal before canvas
  // Uses horizontal layout with proper positioning - compact spacing to fit in viewport
  const dynamicNodes = useMemo(() => {
    const nodeList: Node[] = [];
    const horizontalSpacing = HORIZONTAL_SPACING;
    const verticalSpacing = VERTICAL_SPACING;
    const startX = START_X;
    const startY = START_Y;
    const nodesPerLine = NODES_PER_LINE;

    // Check if this is a supervisor template
    const isSupervisor = config.selectedTemplate?.type === 'supervisor';

    // 0. User Query node (starting point - dummy node, no config needed)
    nodeList.push({
      id: 'userQuery',
      type: 'conversationNode',
      position: { x: startX, y: startY },
      data: {
        id: 'userQuery',
        name: 'User Input',
        type: 'userQuery',
        description: 'Ask your question',
        configured: true, // Always configured, it's just a starting point
      },
    });

    // For Assistant Agent, generate assistant-specific nodes with subflows
    if (isSupervisor) {
      const ragSubflowExpanded = config.expandedSubflows?.retrieval || false;
      const taskSubflowExpanded = config.expandedSubflows?.taskEngine || false;

      // 1. Knowledge Retrieval node (circular - parent of RAG subflow)
      nodeList.push({
        id: 'retrieval',
        type: 'conversationNode',
        position: { x: startX + horizontalSpacing, y: startY },
        data: {
          id: 'retrieval',
          name: 'Knowledge Search',
          type: 'retrieval',
          description: 'RAG Agent - Search knowledge base',
          configured: ragSubflowExpanded ? areRAGSubflowNodesConfigured() : false,
          isSubflowParent: true,
          subflowExpanded: ragSubflowExpanded,
          subflowLabel: ragSubflowExpanded ? '▼ RAG Pipeline' : '▶ RAG Pipeline',
        },
      });

      // If RAG subflow is expanded, add individual RAG sub-nodes
      if (ragSubflowExpanded) {
        const ragConfig: RAGSubflowConfig = {
          selectedStrategy: config.selectedStrategy,
          collectionName: config.collectionName,
          topK: config.topK,
          enableReranking: config.enableReranking,
          selectedRerankerId: config.selectedRerankerId ?? undefined,
          selectedRerankerModel: config.selectedRerankerModel ?? undefined,
          enableLLMGeneration: config.enableLLMGeneration,
          selectedProviderId: config.selectedProviderId ?? undefined,
          selectedModel: config.selectedModel ?? undefined,
        };
        const ragSubflowNodes = generateRAGSubflowNodes('retrieval', startX + horizontalSpacing - 30, startY + 80, ragConfig);
        nodeList.push(...ragSubflowNodes);
      }

      // 2. Task Engine node (circular - parent of Task Agent subflow)
      nodeList.push({
        id: 'taskEngine',
        type: 'conversationNode',
        position: { x: startX + horizontalSpacing * 2, y: startY },
        data: {
          id: 'taskEngine',
          name: 'Task Execution',
          type: 'taskEngine',
          description: 'Task Agent - Execute tasks with tools',
          configured: areTaskSubflowNodesConfigured(),
          isSubflowParent: true,
          subflowExpanded: taskSubflowExpanded,
          subflowLabel: taskSubflowExpanded ? '▼ Task Pipeline' : '▶ Task Pipeline',
        },
      });

      // If Task subflow is expanded, add individual Task sub-nodes
      if (taskSubflowExpanded) {
        const taskConfig: TaskAgentSubflowConfig = {
          enableKnowledgeAssistant: config.enableKnowledgeAssistant,
          selectedSystemPromptId: config.selectedSystemPromptId || undefined,
          selectedTools: config.selectedTools || [],
          tool_instructions: config.tool_instructions || undefined,
        };
        const taskSubflowNodes = generateTaskAgentSubflowNodes('taskEngine', startX + horizontalSpacing * 2 - 30, startY + 80, taskConfig);
        nodeList.push(...taskSubflowNodes);
      }

      // 3. Response Generation node (circular)
      nodeList.push({
        id: 'response',
        type: 'conversationNode',
        position: { x: startX + horizontalSpacing * 3, y: startY },
        data: {
          id: 'response',
          name: 'Final Response',
          type: 'response',
          description: 'Generate final answer',
          configured: true,
        },
      });

      return nodeList;
    }

    // RAG flow continues below...

    // 1. Query Strategy node (formerly Enhancement)
    // Green if: strategy is native OR (strategy is non-native AND provider + model are set)
    const isEnhancementConfigured = config.selectedStrategy === 'native'
      ? (config.configuredNodes?.enhancement || false)
      : (config.configuredNodes?.enhancement && !!config.selectedProviderId && !!config.selectedModel);

    nodeList.push({
      id: 'enhancement',
      type: 'conversationNode',
      position: { x: startX + horizontalSpacing, y: startY },
      data: {
        id: 'enhancement',
        name: 'Query Enhancement',
        type: 'enhancement',
        description: ENHANCEMENT_STRATEGIES.find(s => s.value === config.selectedStrategy)?.label || 'Native RAG',
        configured: isEnhancementConfigured,
      },
    });

    // 2. Search Documents node (formerly Retrieval)
    // Green if: collectionName is set AND retrieval is marked as configured
    // NO DEFAULT COLLECTION - user must explicitly select
    nodeList.push({
      id: 'retrieval',
      type: 'conversationNode',
      position: { x: startX + horizontalSpacing * 2, y: startY },
      data: {
        id: 'retrieval',
        name: 'Search Documents',
        type: 'retrieval',
        description: config.collectionName ? `Collection: ${config.collectionName}` : 'Not configured',
        configured: config.configuredNodes?.retrieval || false, // Green only if user explicitly configured
      },
    });

    // 3. Reranking node (only if enabled)
    // Green if: reranker provider AND model are both selected AND marked as configured
    if (config.enableReranking) {
      // Get provider name for display
      const rerankerProvider = providers?.find(p => p.id === config.selectedRerankerId);
      const rerankerDisplay = config.selectedRerankerModel
        ? `${rerankerProvider?.name || 'Reranker'} (${config.selectedRerankerModel})`
        : config.selectedRerankerId
          ? 'Provider selected'
          : 'Not configured';

      nodeList.push({
        id: 'reranking',
        type: 'conversationNode',
        position: { x: startX + horizontalSpacing * 3, y: startY },
        data: {
          id: 'reranking',
          name: 'Rerank Results',
          type: 'reranking',
          description: rerankerDisplay,
          configured: config.configuredNodes?.reranking || false, // Green only if user explicitly configured
        },
      });
    }

    // 4. Final node: Generate Answer or Raw Output
    const finalNodeX = config.enableReranking
      ? startX + horizontalSpacing * 4
      : startX + horizontalSpacing * 3;

    if (config.enableLLMGeneration) {
      nodeList.push({
        id: 'llm',
        type: 'conversationNode',
        position: { x: finalNodeX, y: startY },
        data: {
          id: 'llm',
          name: 'Generate Answer',
          type: 'llm',
          description: config.selectedModel ? 'Configured' : 'Not configured',
          configured: config.configuredNodes?.llm || false, // Green only if user explicitly configured
        },
      });
    } else {
      nodeList.push({
        id: 'formatter',
        type: 'conversationNode',
        position: { x: finalNodeX, y: startY },
        data: {
          id: 'formatter',
          name: 'Return Documents',
          type: 'formatter',
          description: 'Retrieval only',
          configured: false, // Raw output is default fallback, not user-configured
        },
      });
    }

    return nodeList;
  }, [config]);

  // Dynamic edge generation based on node order
  const dynamicEdges = useMemo(() => {
    const edgeList: Edge[] = [];
    const nodeIds = dynamicNodes.map(n => n.id).filter(id => !id.includes('-')); // Only main flow nodes

    // Create edges between consecutive main flow nodes
    for (let i = 0; i < nodeIds.length - 1; i++) {
      edgeList.push({
        id: `e${i + 1}`,
        source: nodeIds[i],
        target: nodeIds[i + 1],
        type: 'default',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#51cf66' },
        style: {
          stroke: '#51cf66',
          strokeWidth: 2,
        },
      });
    }

    // Add RAG subflow edges if expanded
    if (config.expandedSubflows?.retrieval) {
      const ragConfig: RAGSubflowConfig = {
        selectedStrategy: config.selectedStrategy,
        collectionName: config.collectionName,
        topK: config.topK,
        enableReranking: config.enableReranking,
        selectedRerankerId: config.selectedRerankerId ?? undefined,
        selectedRerankerModel: config.selectedRerankerModel ?? undefined,
        enableLLMGeneration: config.enableLLMGeneration,
        selectedProviderId: config.selectedProviderId ?? undefined,
        selectedModel: config.selectedModel ?? undefined,
      };
      const ragSubflowEdges = generateRAGSubflowEdges('retrieval', ragConfig);
      edgeList.push(...ragSubflowEdges);
    }

    // Add Task Agent subflow edges if expanded
    if (config.expandedSubflows?.taskEngine) {
      const taskSubflowEdges = generateTaskAgentSubflowEdges('taskEngine');
      edgeList.push(...taskSubflowEdges);
    }

    return edgeList;
  }, [dynamicNodes, config]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [configPanelOpen, setConfigPanelOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);

  // Update nodes and edges whenever config changes
  useEffect(() => {
    setNodes(dynamicNodes);
    setEdges(dynamicEdges);
  }, [dynamicNodes, dynamicEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    // Single click opens config panel for all configurable nodes
    const configurableNodes = ['userQuery', 'settings', 'enhancement', 'retrieval', 'reranking', 'llm', 'formatter', 'assistant', 'taskEngine'];

    if (configurableNodes.includes(node.data?.type)) {
      setSelectedNodeId(node.id);
      setConfigPanelOpen(true);
    }
  }, []);

  const handleNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
    // Check if this is a subflow parent node (Knowledge Retrieval or Task Engine)
    if (node.data?.isSubflowParent) {
      if (node.id === 'retrieval') {
        // Open RAG subflow - close Task Engine if open
        const isCurrentlyExpanded = config.expandedSubflows?.retrieval || false;
        setConfig(prev => ({
          ...prev,
          expandedSubflows: {
            retrieval: !isCurrentlyExpanded,
            taskEngine: false, // Close the other subflow to prevent overlap
          },
        }));
        notifications.show({
          title: isCurrentlyExpanded ? 'RAG Agent Collapsed' : 'RAG Agent Expanded',
          message: isCurrentlyExpanded ? 'Hiding RAG pipeline steps' : 'Showing RAG pipeline steps',
          color: 'blue',
        });
      } else if (node.id === 'taskEngine') {
        // Open Task Agent subflow - close RAG if open
        const isCurrentlyExpanded = config.expandedSubflows?.taskEngine || false;
        setConfig(prev => ({
          ...prev,
          expandedSubflows: {
            retrieval: false, // Close the other subflow to prevent overlap
            taskEngine: !isCurrentlyExpanded,
          },
        }));
        notifications.show({
          title: isCurrentlyExpanded ? 'Task Agent Collapsed' : 'Task Agent Expanded',
          message: isCurrentlyExpanded ? 'Hiding task pipeline steps' : 'Showing task pipeline steps',
          color: 'blue',
        });
      }
    } else {
      // Regular node configuration
      setSelectedNodeId(node.id);
      setConfigPanelOpen(true);
    }
  }, [config.expandedSubflows]);

  const handleCanvasContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenu({ x: event.clientX, y: event.clientY });
  }, []);

  const handleEnableReranking = () => {
    setConfig(prev => ({
      ...prev,
      enableReranking: true,
    }));
    setContextMenu(null);
    notifications.show({
      title: 'Reranking Enabled',
      message: 'Rerank Results node added to pipeline',
      color: 'blue',
      icon: <IconCheck size={16} />,
    });
  };

  const handleDisableReranking = () => {
    setConfig(prev => ({
      ...prev,
      enableReranking: false,
    }));
    setContextMenu(null);
  };

  const handleEnableLLMGeneration = () => {
    setConfig(prev => ({
      ...prev,
      enableLLMGeneration: true,
    }));
    setContextMenu(null);
    notifications.show({
      title: 'LLM Generation Enabled',
      message: 'Generate Answer node added to pipeline',
      color: 'blue',
      icon: <IconCheck size={16} />,
    });
  };

  const handleDisableLLMGeneration = () => {
    setConfig(prev => ({
      ...prev,
      enableLLMGeneration: false,
    }));
    setContextMenu(null);
  };

  const handleSaveNodeConfig = (nodeId: string, nodeConfig: any) => {
    console.log('[handleSaveNodeConfig] nodeId:', nodeId, 'nodeConfig:', nodeConfig);

    setConfig(prev => {
      const newConfiguredNodes = {
        ...prev.configuredNodes,
        [nodeId]: true,  // Mark this specific node as configured
      };

      // If this is a retrieval subflow node, also mark the parent 'retrieval' as configured
      if (nodeId.startsWith('retrieval-')) {
        newConfiguredNodes.retrieval = true;
      }

      // If this is a taskEngine subflow node, also mark the parent 'taskEngine' as configured
      if (nodeId.startsWith('taskEngine-')) {
        newConfiguredNodes.taskEngine = true;
      }

      const newConfig = {
        ...prev,           // Preserve ALL previous config
        ...nodeConfig,     // Merge in ONLY the node-specific properties
        configuredNodes: newConfiguredNodes,
      };

      console.log('[handleSaveNodeConfig] Updated configuredNodes:', newConfiguredNodes);

      return newConfig;
    });

    setConfigPanelOpen(false);
    notifications.show({
      title: 'Configuration Saved',
      message: `${nodeId} node configured successfully`,
      color: 'green',
    });
  };

  const handleSelectTemplate = (template: ConversationTemplate, selectedOptionals: string[]) => {
    // Apply template configuration to the canvas
    setConfig(prev => ({
      ...prev,
      selectedTemplate: template, // Store the template for node generation
      selectedStrategy: template.defaultConfig.selectedStrategy,
      enableReranking: selectedOptionals.includes('reranking') || template.defaultConfig.enableReranking,
      enableLLMGeneration: selectedOptionals.includes('llm') || template.defaultConfig.enableLLMGeneration,
      enableKnowledgeAssistant: template.type === 'supervisor', // Auto-enable for supervisor templates
      // Mark enhancement as configured only if it's native strategy
      // For non-native strategies, user must configure provider and model
      configuredNodes: {
        ...prev.configuredNodes,
        enhancement: template.defaultConfig.selectedStrategy === 'native', // Only auto-configure for native
        assistant: template.type === 'supervisor' ? true : undefined, // Assistant config for supervisor
      },
    }));

    // Mark template as selected to close the modal and show the canvas
    setTemplateSelected(true);

    notifications.show({
      title: 'Template Applied',
      message: `${template.name} template loaded. Configure the nodes as needed.`,
      color: 'blue',
      icon: <IconRefresh size={16} />,
    });
  };

  const handleBackToWizard = () => {
    navigate(paths.dashboard.apps.conversationCreate);
  };

  const handleCreateConversation = async () => {
    try {
      setIsCreating(true);

      // Validate required fields
      if (!config.conversationName.trim()) {
        notifications.show({
          title: 'Error',
          message: 'Conversation name is required',
          color: 'red',
        });
        return;
      }

      if (config.selectedStrategy !== 'native' && !config.conversationDescription.trim()) {
        notifications.show({
          title: 'Error',
          message: 'Description is required for non-native strategies',
          color: 'red',
        });
        return;
      }

      if (!config.collectionName) {
        notifications.show({
          title: 'Error',
          message: 'Collection name is required',
          color: 'red',
        });
        return;
      }

      // Validate enhancement strategy requirements
      // custom_variants doesn't require LLM since user provides pre-defined variants
      if (config.selectedStrategy !== 'native' && config.selectedStrategy !== 'custom_variants' && (!config.selectedProviderId || !config.selectedModel)) {
        notifications.show({
          title: 'Error',
          message: 'LLM provider and model are required for this enhancement strategy',
          color: 'red',
        });
        return;
      }

      if (config.enableLLMGeneration && (!config.selectedProviderId || !config.selectedModel)) {
        notifications.show({
          title: 'Error',
          message: 'LLM provider and model are required',
          color: 'red',
        });
        return;
      }

      // Create conversation via API - Match wizard payload structure exactly
      const token = localStorage.getItem('jwt_token');

      // Determine final strategy based on available configuration
      // custom_variants doesn't require LLM provider/model
      // Other non-native strategies require both provider AND model
      let finalStrategy = 'native';
      if (config.selectedStrategy === 'custom_variants') {
        finalStrategy = 'custom_variants';
      } else if (config.selectedStrategy !== 'native' && config.selectedProviderId && config.selectedModel) {
        finalStrategy = config.selectedStrategy;
      }

      const payload: any = {
        name: config.conversationName.trim(),
        description: config.conversationDescription.trim() || null,
        // Enhancement configuration - ALWAYS include
        enhancement: {
          strategy: finalStrategy,
          provider: finalStrategy !== 'native' && config.selectedProviderId && config.selectedModel ? {
            id: config.selectedProviderId,
            model_name: config.selectedModel,
          } : null,
        },
        // Vector database configuration
        vector_database: {
          collection_name: config.collectionName,
          top_k: config.topK,
        },
        // Reranker configuration - ALWAYS include with enabled flag
        reranker: {
          enabled: config.enableReranking,
          provider: config.enableReranking && config.selectedRerankerId && config.selectedRerankerModel ? {
            id: config.selectedRerankerId,
            model_name: config.selectedRerankerModel,
          } : null,
          relevance_threshold: 0.5, // Default threshold
        },
        // Answer generation configuration - ALWAYS include with enabled flag
        answer_generation: {
          enabled: config.enableLLMGeneration && config.selectedProviderId && config.selectedModel ? true : false,
          provider: config.enableLLMGeneration && config.selectedProviderId && config.selectedModel ? {
            id: config.selectedProviderId,
            model_name: config.selectedModel,
          } : null,
        },
        // Assistant configuration - Preserve tasks even when disabled
        assistant_config: (() => {
          console.log('[CREATE] Assistant config state:', {
            enableKnowledgeAssistant: config.enableKnowledgeAssistant,
            selectedSystemPrompt: config.selectedSystemPrompt,
            systemPromptTasks: config.systemPromptTasks,
            selectedSystemPromptId: config.selectedSystemPromptId,
          });

          // Build system_prompt_tasks regardless of enabled state
          // This preserves tasks when switching between RAG and Assistant modes
          let tasks = null;

          // Priority 1: Use selectedSystemPrompt if available
          if (config.selectedSystemPrompt) {
            tasks = [{
              id: config.selectedSystemPrompt.id || '',
              title: config.selectedSystemPrompt.title || config.selectedSystemPrompt.name || '',
              content: config.selectedSystemPrompt.content || config.selectedSystemPrompt.system_prompt || '',
              is_active: config.selectedSystemPrompt.is_active !== false,
            }];
          }
          // Priority 2: Use systemPromptTasks if available
          else if (config.systemPromptTasks && config.systemPromptTasks.length > 0) {
            tasks = config.systemPromptTasks.map((task: any) => ({
              id: task.id || '',
              title: task.title || task.name || '',
              content: task.content || task.system_prompt || '',
              is_active: task.is_active !== false,
            }));
          }

          return {
            enabled: config.enableKnowledgeAssistant || false,
            system_prompt_tasks: tasks, // Preserved regardless of enabled state
          };
        })(),
      };

      console.log('[handleCreateConversation] Payload:', JSON.stringify(payload, null, 2));

      const response = await fetch(apiUtils.buildApiUrl('/conversations'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        notifications.show({
          title: 'Success',
          message: 'Conversation created successfully',
          color: 'green',
          icon: <IconCheck size={16} />,
        });
        navigate(paths.dashboard.apps.conversation(data.id));
      } else {
        throw new Error('Failed to create conversation');
      }
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: error instanceof Error ? error.message : 'Failed to create conversation',
        color: 'red',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const configuredCount = nodes.filter(n => n.data?.configured).length;

  // If template not selected yet, only show template selector
  if (!templateSelected) {
    return (
      <Page title="Conversation Agent Pipeline Builder">
        <PageHeader title="Conversation Agent Pipeline Builder" breadcrumbs={breadcrumbs} />
        <ConversationTemplateSelector
          opened={true}
          onClose={() => navigate(paths.dashboard.apps.knowledgeSearch)}
          onSelectTemplate={handleSelectTemplate}
        />
      </Page>
    );
  }

  return (
    <Page title="Conversation Agent Pipeline Builder">
      <PageHeader title="Conversation Agent Pipeline Builder" breadcrumbs={breadcrumbs} />

      <Container fluid my="md" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)' }}>
        <Stack gap="md" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <Paper shadow="sm" p="md">
            <Group justify="space-between" align="center">
              <div>
                <Title order={4}>Build Conversation Agent Pipeline</Title>
                <Group gap="sm" mt="xs">
                  <Badge variant="dot" color="blue">
                    {configuredCount}/{nodes.length} configured
                  </Badge>
                  <Group gap="xs">
                    <Text size="sm" c="dimmed">
                      👆 Double-click nodes to configure
                    </Text>
                    <Text size="sm" c="dimmed">
                      •
                    </Text>
                    <Text size="sm" c="dimmed">
                      🖱️ Right-click to add/remove nodes
                    </Text>
                  </Group>
                </Group>
              </div>
              <Group>
                <Button
                  variant="light"
                  leftSection={<IconRefresh size={16} />}
                  onClick={() => setTemplateSelected(false)}
                >
                  Load Conversation Agent Template
                </Button>
                <Button variant="default" leftSection={<IconArrowLeft size={16} />} onClick={handleBackToWizard}>
                  Back to Conversation Agent Wizard
                </Button>
              </Group>
            </Group>
          </Paper>

          <Paper withBorder p="0" radius="md" style={{ flex: 1, overflow: 'hidden', minHeight: 0, position: 'relative' }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              onNodeClick={handleNodeClick}
              onNodeDoubleClick={handleNodeDoubleClick}
              onContextMenu={handleCanvasContextMenu}
              fitView
            >
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              <Controls />
              <MiniMap />
            </ReactFlow>


            {/* Context Menu for adding disabled nodes */}
            {contextMenu && (
              <div style={{
                position: 'fixed',
                top: contextMenu.y,
                left: contextMenu.x,
                backgroundColor: 'white',
                border: '1px solid #e0e0e0',
                borderRadius: '6px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                zIndex: 200,
                minWidth: '200px',
              }}>
                <Stack gap="0" style={{ padding: '4px 0' }}>
                  {!config.enableReranking && (
                    <Button
                      variant="subtle"
                      justify="flex-start"
                      fullWidth
                      size="xs"
                      onClick={handleEnableReranking}
                      style={{ borderRadius: 0, padding: '8px 12px' }}
                    >
                      ➕ Add Rerank Results Node
                    </Button>
                  )}
                  {config.enableReranking && (
                    <Button
                      variant="subtle"
                      justify="flex-start"
                      fullWidth
                      size="xs"
                      color="red"
                      onClick={handleDisableReranking}
                      style={{ borderRadius: 0, padding: '8px 12px' }}
                    >
                      ❌ Remove Rerank Results Node
                    </Button>
                  )}

                  {!config.enableLLMGeneration && (
                    <>
                      <Button
                        variant="subtle"
                        justify="flex-start"
                        fullWidth
                        size="xs"
                        onClick={() => {
                          if (config.selectedTemplate?.type === 'supervisor') {
                            notifications.show({
                              title: '⚠️ Not Recommended',
                              message: 'In Supervisor Agent mode, LLM generation is not recommended. The system needs raw documents context for the Task Agent to execute tasks effectively.',
                              color: 'yellow',
                              autoClose: 5000,
                            });
                          }
                          handleEnableLLMGeneration();
                        }}
                        style={{ borderRadius: 0, padding: '8px 12px' }}
                      >
                        ➕ Add Generate Answer Node
                        {config.selectedTemplate?.type === 'supervisor' && ' (⚠️ Not Recommended)'}
                      </Button>
                    </>
                  )}
                  {config.enableLLMGeneration && (
                    <Button
                      variant="subtle"
                      justify="flex-start"
                      fullWidth
                      size="xs"
                      color="red"
                      onClick={handleDisableLLMGeneration}
                      style={{ borderRadius: 0, padding: '8px 12px' }}
                    >
                      ❌ Remove Generate Answer Node
                    </Button>
                  )}
                </Stack>
              </div>
            )}

            {/* Close context menu when clicking anywhere */}
            {contextMenu && (
              <div
                style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  zIndex: 199,
                }}
                onClick={() => setContextMenu(null)}
              />
            )}

            {/* Configuration Panel - Right Side */}
            <ConversationNodeConfigPanel
              node={nodes.find(n => n.id === selectedNodeId) || null}
              opened={configPanelOpen}
              onClose={() => setConfigPanelOpen(false)}
              onSave={handleSaveNodeConfig}
              providers={providers}
              collections={collections}
              config={config}
            />
          </Paper>

          <Group justify="flex-end">
            <Button variant="default" onClick={handleBackToWizard}>
              Cancel
            </Button>
            <Button
              color="green"
              leftSection={<IconCheck size={16} />}
              onClick={() => {
                // Validate all required nodes are configured BEFORE opening modal
                if (!config.selectedStrategy) {
                  notifications.show({
                    title: 'Configuration Incomplete',
                    message: 'Query Strategy must be configured',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                // Validate enhancement node configuration
                if (config.selectedStrategy !== 'native' && (!config.selectedProviderId || !config.selectedModel)) {
                  notifications.show({
                    title: 'Configuration Incomplete',
                    message: 'Query Strategy requires LLM provider and model for non-native strategies. Please configure the Query Strategy node.',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (!config.collectionName || !config.topK) {
                  console.error('[ERROR] Validation failed:', {
                    collectionName: config.collectionName,
                    collectionNameEmpty: !config.collectionName,
                    topK: config.topK,
                    topKEmpty: !config.topK,
                  });
                  notifications.show({
                    title: 'Configuration Incomplete',
                    message: 'Document Search must be configured (select collection and Top K)',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (config.enableReranking && !config.configuredNodes?.reranking) {
                  notifications.show({
                    title: 'Configuration Incomplete',
                    message: 'Rerank Results is enabled but not configured (select provider and model)',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (config.enableLLMGeneration && !config.configuredNodes?.llm) {
                  notifications.show({
                    title: 'Configuration Incomplete',
                    message: 'Generate Answer is enabled but not configured (select provider and model)',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                // All validations passed, now open the basic info modal
                setBasicInfoModalOpen(true);
              }}
              loading={isCreating}
            >
              Create Conversation
            </Button>
          </Group>
        </Stack>
      </Container>

      {/* Basic Info Modal - Shown when user clicks Create Conversation */}
      <Modal
        opened={basicInfoModalOpen}
        onClose={() => setBasicInfoModalOpen(false)}
        title="Conversation Agent Pipeline Details"
        size="sm"
        centered
      >
        <Stack gap="md">
          <TextInput
            label="Conversation Agent Pipeline Name"
            placeholder="e.g., SSL Configuration Help Conversation Agent Pipeline"
            value={config.conversationName}
            onChange={(e) => setConfig({ ...config, conversationName: e.currentTarget.value })}
            required
            withAsterisk
            description="Give your conversation agent pipeline a descriptive name"
          />

          <Textarea
            label={config.selectedStrategy !== 'native' ? "Description (Required for Query Enhancement)" : "Description (Optional)"}
            placeholder={config.selectedStrategy !== 'native'
              ? "Describe the domain/topic to help enhance queries (e.g., 'MuleSoft API documentation conversation agent pipeline')"
              : "Brief description of what this conversation is about..."}
            value={config.conversationDescription}
            onChange={(e) => setConfig({ ...config, conversationDescription: e.currentTarget.value })}
            minRows={2}
            maxRows={4}
            required={config.selectedStrategy !== 'native'}
            withAsterisk={config.selectedStrategy !== 'native'}
            error={config.selectedStrategy !== 'native' && !config.conversationDescription.trim() ? 'Description is required when using query enhancement conversation agent pipeline' : undefined}
            description={config.selectedStrategy !== 'native' ? "This helps the AI understand the domain and provide better query enhancements" : "Optional description for context"}
          />

          <Group justify="flex-end">
            <Button
              variant="subtle"
              onClick={() => {
                setBasicInfoModalOpen(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (!config.conversationName.trim()) {
                  notifications.show({
                    title: 'Error',
                    message: 'Conversation name is required',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (config.selectedStrategy !== 'native' && !config.conversationDescription.trim()) {
                  notifications.show({
                    title: 'Error',
                    message: 'Description is required when using query enhancement strategies',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                // Validate all required nodes are configured
                if (!config.configuredNodes?.enhancement) {
                  notifications.show({
                    title: 'Error',
                    message: 'Query Strategy must be configured',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (!config.configuredNodes?.retrieval) {
                  console.error('[Validation Failed] retrieval node not configured:', {
                    'configuredNodes': config.configuredNodes,
                    'configuredNodes.retrieval': config.configuredNodes?.retrieval,
                    'collectionName': config.collectionName,
                    'configuredNodes keys': Object.keys(config.configuredNodes || {}),
                    'configuredNodes values': Object.values(config.configuredNodes || {}),
                  });
                  notifications.show({
                    title: 'Error',
                    message: `Document Search (collection) must be configured. Current status: retrieval=${config.configuredNodes?.retrieval}, collection=${config.collectionName}`,
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (config.enableReranking && !config.configuredNodes?.reranking) {
                  notifications.show({
                    title: 'Error',
                    message: 'Rerank Results is enabled but not configured',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                if (config.enableLLMGeneration && !config.configuredNodes?.llm) {
                  notifications.show({
                    title: 'Error',
                    message: 'Generate Answer is enabled but not configured',
                    color: 'red',
                    icon: <IconAlertCircle size={16} />,
                  });
                  return;
                }

                setBasicInfoModalOpen(false);
                handleCreateConversation();
              }}
              color="blue"
            >
              Create Conversation Agent
            </Button>
          </Group>
        </Stack>
      </Modal>

    </Page>
  );
}

export function ConversationCanvasBuilder() {
  return (
    <ReactFlowProvider>
      <ConversationCanvasContent />
    </ReactFlowProvider>
  );
}
