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
import { RAGSubflowConfig, generateRAGSubflowNodes, generateRAGSubflowEdges } from './RAGSubflow';
import { TaskAgentSubflowConfig, generateTaskAgentSubflowNodes, generateTaskAgentSubflowEdges } from './TaskAgentSubflow';

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
    collectionName: 'LongTermMemory', // Default collection
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

  // Positioning constants for the canvas
  const HORIZONTAL_SPACING = 160; // Compact spacing to fit all nodes without scrolling (max 5 nodes = 30 + 4*160 = 670px)
  const VERTICAL_SPACING = 200;
  const START_X = 30;
  const START_Y = 50;
  const NODES_PER_LINE = 4;

  // Helper function to check if all RAG subflow nodes are configured
  const areRAGSubflowNodesConfigured = (): boolean => {
    // Enhancement is configured if selectedStrategy is set AND
    // if it's non-native, LLM provider and model must also be set
    let enhancementConfigured = !!config.selectedStrategy;
    if (enhancementConfigured && config.selectedStrategy !== 'native') {
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
        name: 'User Query',
        type: 'userQuery',
        description: 'Your question',
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
          name: 'Knowledge Retrieval',
          type: 'retrieval',
          description: 'RAG Agent - Search knowledge base',
          configured: areRAGSubflowNodesConfigured(),
          isSubflowParent: true,
          subflowExpanded: ragSubflowExpanded,
          subflowLabel: ragSubflowExpanded ? '▼ RAG Agent' : '▶ RAG Agent',
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
          name: 'Task Engine',
          type: 'taskEngine',
          description: 'Task Agent - System Prompts & Execution',
          configured: areTaskSubflowNodesConfigured(),
          isSubflowParent: true,
          subflowExpanded: taskSubflowExpanded,
          subflowLabel: taskSubflowExpanded ? '▼ Task Agent' : '▶ Task Agent',
        },
      });

      // If Task subflow is expanded, add individual Task sub-nodes
      if (taskSubflowExpanded) {
        const taskConfig: TaskAgentSubflowConfig = {
          enableKnowledgeAssistant: config.enableKnowledgeAssistant,
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
          name: 'Response',
          type: 'response',
          description: 'Generate final response',
          configured: true,
        },
      });

      return nodeList;
    }

    // RAG flow continues below...

    // 1. Query Strategy node (formerly Enhancement)
    // Green if: selectedStrategy is marked as configured in configuredNodes
    nodeList.push({
      id: 'enhancement',
      type: 'conversationNode',
      position: { x: startX + horizontalSpacing, y: startY },
      data: {
        id: 'enhancement',
        name: 'Query Strategy',
        type: 'enhancement',
        description: ENHANCEMENT_STRATEGIES.find(s => s.value === config.selectedStrategy)?.label || 'Native RAG',
        configured: config.configuredNodes?.enhancement || false, // Green if user has confirmed
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
        markerEnd: { type: 'arrowclosed', color: '#51cf66', scale: 0.5 },
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
    setConfig(prev => ({
      ...nodeConfig,
      configuredNodes: {
        ...prev.configuredNodes,
        [nodeId]: true, // Mark this node as configured when user saves
      },
    }));
    setConfigPanelOpen(false);
    // Nodes update automatically via useMemo when config changes
    notifications.show({
      title: 'Configuration Saved',
      message: 'Node configuration updated',
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
      // Mark enhancement as configured since template selected the strategy
      configuredNodes: {
        ...prev.configuredNodes,
        enhancement: true, // Enhancement is configured in both RAG and Supervisor modes
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

      if (config.enableLLMGeneration && (!config.selectedProviderId || !config.selectedModel)) {
        notifications.show({
          title: 'Error',
          message: 'LLM provider and model are required',
          color: 'red',
        });
        return;
      }

      // Create conversation via API
      const token = localStorage.getItem('jwt_token');
      const payload: any = {
        name: config.conversationName.trim(),
      };

      if (config.conversationDescription.trim()) {
        payload.description = config.conversationDescription.trim();
      }

      if (config.selectedStrategy && config.selectedStrategy !== 'none') {
        payload.enhancement_strategy = config.selectedStrategy;
      }

      payload.collection_name = config.collectionName.trim();
      payload.enable_reranking = config.enableReranking;
      payload.enable_llm_generation = config.enableLLMGeneration;
      payload.enable_knowledge_assistant = config.enableKnowledgeAssistant;
      payload.top_k = config.topK;

      if (config.selectedProviderId) {
        payload.llm_provider_id = config.selectedProviderId;
      }

      if (config.selectedModel) {
        payload.llm_model_name = config.selectedModel;
      }

      if (config.enableReranking && config.selectedRerankerId) {
        payload.reranker_provider_id = config.selectedRerankerId;
      }

      if (config.enableReranking && config.selectedRerankerModel) {
        payload.reranker_model_name = config.selectedRerankerModel;
      }

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

                if (!config.collectionName || !config.topK) {
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
        title="Conversation Details"
        size="sm"
        centered
      >
        <Stack gap="md">
          <TextInput
            label="Conversation Name"
            placeholder="e.g., SSL Configuration Help"
            value={config.conversationName}
            onChange={(e) => setConfig({ ...config, conversationName: e.currentTarget.value })}
            required
            withAsterisk
            description="Give your conversation a descriptive name"
          />

          <Textarea
            label={config.selectedStrategy !== 'native' ? "Description (Required for Query Enhancement)" : "Description (Optional)"}
            placeholder={config.selectedStrategy !== 'native'
              ? "Describe the domain/topic to help enhance queries (e.g., 'MuleSoft API documentation')"
              : "Brief description of what this conversation is about..."}
            value={config.conversationDescription}
            onChange={(e) => setConfig({ ...config, conversationDescription: e.currentTarget.value })}
            minRows={2}
            maxRows={4}
            required={config.selectedStrategy !== 'native'}
            withAsterisk={config.selectedStrategy !== 'native'}
            error={config.selectedStrategy !== 'native' && !config.conversationDescription.trim() ? 'Description is required when using query enhancement' : undefined}
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
                  notifications.show({
                    title: 'Error',
                    message: 'Document Search (collection) must be configured',
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
              Create Conversation
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
