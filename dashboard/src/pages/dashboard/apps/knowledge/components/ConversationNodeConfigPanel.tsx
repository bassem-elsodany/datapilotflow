/**
 * Conversation Node Configuration Panel
 *
 * Right-side panel for configuring conversation pipeline nodes
 * EXACTLY SAME as job pipeline's NodeConfigPanel
 */

import { SystemPromptManager } from '@/components/system-prompt-manager';
import { useGetTools } from '@/api/resources/tools';
import { apiUtils } from '@/config';
import { ActionIcon, Badge, Box, Button, Card, Divider, Group, NumberInput, Paper, Select, Stack, Switch, Text, TextInput, Textarea, Alert, Loader } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle, IconCheck, IconChevronDown, IconChevronUp, IconX, IconSparkles, IconDots } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Node } from 'reactflow';

interface ConversationNodeData {
  id: string;
  name: string;
  type: 'userQuery' | 'settings' | 'enhancement' | 'retrieval' | 'reranking' | 'llm' | 'formatter' | 'assistant' | 'taskEngine' | 'response';
  description: string;
  configured: boolean;
}

interface ConversationNodeConfigPanelProps {
  node: Node<ConversationNodeData> | null;
  opened: boolean;
  onClose: () => void;
  onSave: (nodeId: string, config: any) => void;
  providers?: any[];
  collections?: any[];
  config?: any;
}

// Enhanced strategy definitions with detailed information
const ENHANCEMENT_STRATEGIES = [
  {
    value: 'native',
    label: 'Native RAG',
    description: 'Traditional RAG without query enhancement',
    details: 'Your query is sent directly to the retrieval system without any modifications. Best for simple, well-formed questions and fastest performance.',
    useCases: ['Simple lookups', 'Direct questions', 'Performance-critical scenarios'],
    pros: ['Fastest performance', 'Most straightforward', 'No added complexity'],
    cons: ['May miss relevant documents', 'Limited coverage', 'Depends on exact wording'],
    color: 'blue',
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Searches directly with: "How to configure SSL certificates in Apache?"'
    }
  },
  {
    value: 'augmented',
    label: 'Augmented (Best Coverage)',
    description: 'Systematic transformations for maximum coverage',
    details: 'Applies 4 specific transformation techniques: (1) Synonym Expansion, (2) Query Expansion (add implicit concepts), (3) Query Contraction (focus on core), (4) Technical Reformulation. Uses RRF to merge all variants.',
    useCases: ['Maximum coverage needed', 'Comprehensive search', 'Documents use varied styles'],
    pros: ['Systematic coverage', 'Fills retrieval gaps', 'Explores all angles'],
    cons: ['Slightly slower than Native', 'Uses more tokens'],
    color: 'green',
    example: {
      original: 'SSL configuration in production',
      output: 'Transforms systematically:\n1. Original: "SSL configuration in production"\n2. Synonym: "secure socket layer setup in production environment"\n3. Expanded: "SSL certificate configuration HTTPS production deployment"\n4. Contracted: "SSL production config"\n5. Technical: "TLS security settings live environment"'
    }
  },
  {
    value: 'custom_variants',
    label: 'Custom Variants',
    description: 'User-provided query variations (no LLM cost)',
    details: 'Accepts pre-defined query variants from you without any LLM enhancement. Searches all variants in parallel and uses RRF to merge results. Perfect for when you know exactly what variations to search.',
    useCases: ['Multi-language search', 'Pre-computed variants', 'Zero LLM cost', 'Full control over variations'],
    pros: ['No LLM cost', 'Full user control', 'Fast (parallel search)', 'Predictable results'],
    cons: ['Requires manual variant creation', 'No AI suggestions', 'Quality depends on user input'],
    color: 'cyan',
    example: {
      original: 'Send as list: ["SSL configuration", "TLS setup", "HTTPS encryption"]',
      output: 'Uses your variants:\n1. "SSL configuration"\n2. "TLS setup"\n3. "HTTPS encryption"\n\nSearches all in parallel with RRF fusion. No LLM enhancement.'
    }
  },
  {
    value: 'multi_query',
    label: 'Multi-Query',
    description: 'Rephrase the same question in different ways',
    details: 'Generates 3-5 alternative phrasings of the SAME question using different vocabulary and wording. Uses RRF to merge results from all phrasings.',
    useCases: ['Documents use varied terminology', 'Unknown exact terms', 'Vocabulary mismatches'],
    pros: ['Linguistic flexibility', 'Handles synonyms', 'Matches varied writing styles'],
    cons: ['Same semantic space', 'May miss edge cases'],
    color: 'teal',
    example: {
      original: 'Salesforce platform event listener config',
      output: 'Rephrases in different ways:\n1. "How to configure Salesforce platform event listeners?"\n2. "Salesforce platform event subscription setup"\n3. "Setting up Salesforce platform event handlers"\n4. "Salesforce platform event listener configuration guide"\n5. "Steps to configure Salesforce event listeners"'
    }
  },
  {
    value: 'hyde',
    label: 'HyDE (Hypothetical Document Embeddings)',
    description: 'Generate hypothetical answer for better matching',
    details: 'Creates a hypothetical answer to your question, then searches for documents similar to that answer. Excellent for semantic similarity matching.',
    useCases: ['Answer-seeking queries', 'When you know what format you want', 'Semantic search'],
    pros: ['Excellent semantic matching', 'Finds answer-like docs', 'Good for how-to questions'],
    cons: ['Requires good LLM', 'May hallucinate'],
    color: 'grape',
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Generates hypothetical answer:\n"To configure SSL in Apache, first install mod_ssl, then create a VirtualHost with SSLEngine on, SSLCertificateFile pointing to your cert, and SSLCertificateKeyFile for the private key. Restart Apache to apply changes."\n\nThen searches for documents similar to this answer.'
    }
  },
  {
    value: 'decomposition',
    label: 'Decomposition',
    description: 'Break complex queries into sub-questions',
    details: 'Splits your complex question into simpler sub-questions. Each sub-question is processed separately for comprehensive coverage. Uses RRF to merge results from all sub-queries.',
    useCases: ['Complex multi-part questions', 'Research tasks', 'Thorough analysis needed'],
    pros: ['Handles complexity', 'RRF merges sub-queries', 'Comprehensive results'],
    cons: ['Slowest option', 'Most expensive'],
    color: 'orange',
    example: {
      original: 'How to configure SSL certificates in Apache?',
      output: 'Breaks down into sub-questions:\n1. "What are the prerequisites for SSL in Apache?"\n2. "How to generate or obtain SSL certificates?"\n3. "What are the Apache SSL configuration directives?"\n4. "How to test and verify SSL configuration?"'
    }
  },
];

type EnhancementStrategy = typeof ENHANCEMENT_STRATEGIES[0];

export function ConversationNodeConfigPanel({
  node,
  opened,
  onClose,
  onSave,
  providers = [],
  collections = [],
  config = {},
}: ConversationNodeConfigPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [localConfig, setLocalConfig] = useState(config);
  const { data: tools, isLoading: toolsLoading } = useGetTools();

  useEffect(() => {
    if (opened && node) {
      setIsExpanded(true);
      // In supervisor mode, force selectedStrategy to custom_variants
      const isSupervisor = node.data.type === 'enhancement' && config.selectedTemplate?.type === 'supervisor';
      const configToSet = isSupervisor
        ? { ...config, selectedStrategy: 'custom_variants' }
        : config;
      setLocalConfig(configToSet);
    }
  }, [node, opened, config]);

  if (!opened || !node) return null;

  // Validate node configuration based on node type
  const validateNodeConfig = (): { valid: boolean; error?: string } => {
    const nodeType = node.data.type;

    switch (nodeType) {
      case 'userQuery':
        // User query doesn't need validation, it's just a starting point
        return { valid: true };

      case 'enhancement':
        // Enhancement must have a strategy selected
        if (!localConfig.selectedStrategy) {
          return { valid: false, error: 'Please select a query strategy' };
        }
        return { valid: true };

      case 'retrieval':
        // Retrieval must have collection AND topK
        if (!localConfig.collectionName) {
          return { valid: false, error: 'Please select a vector collection' };
        }
        if (!localConfig.topK || localConfig.topK < 1) {
          return { valid: false, error: 'Please set Top K to at least 1' };
        }
        return { valid: true };

      case 'reranking':
        // If reranking is enabled, both provider and model required
        if (localConfig.enableReranking) {
          if (!localConfig.selectedRerankerId) {
            return { valid: false, error: 'Please select a reranker provider (Specialized or LLM)' };
          }
          if (!localConfig.selectedRerankerModel) {
            return { valid: false, error: 'Please select a reranker model' };
          }
        }
        return { valid: true };

      case 'llm':
        // If LLM is enabled, both provider and model required
        if (localConfig.enableLLMGeneration) {
          if (!localConfig.selectedProviderId) {
            return { valid: false, error: 'Please select an LLM provider' };
          }
          if (!localConfig.selectedModel) {
            return { valid: false, error: 'Please select an LLM model' };
          }
        }
        return { valid: true };

      default:
        return { valid: true };
    }
  };

  const handleSave = () => {
    const validation = validateNodeConfig();

    if (!validation.valid) {
      notifications.show({
        title: 'Configuration Incomplete',
        message: validation.error || 'Please complete all required fields',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
      return;
    }

    // Remove configuredNodes and expandedSubflows from localConfig before saving
    // These should only be managed by the canvas, not passed from the panel
    const { configuredNodes, expandedSubflows, selectedTemplate, ...configToSave } = localConfig;

    // Force enableKnowledgeAssistant to false in RAG mode, true in supervisor mode
    if (config?.selectedTemplate?.type === 'rag') {
      configToSave.enableKnowledgeAssistant = false;
    } else if (config?.selectedTemplate?.type === 'supervisor') {
      configToSave.enableKnowledgeAssistant = true;
    }

    console.log('[handleSave] Saving config without configuredNodes:', {
      nodeId: node.id,
      nodeType: node.data.type,
      configToSave,
    });

    onSave(node.id, configToSave);
    onClose();
  };

  const getNodeDisplayName = (type: string): string => {
    const names: Record<string, string> = {
      userQuery: 'User Query',
      settings: 'Conversation Settings',
      enhancement: 'Query Strategy',
      retrieval: 'Document Search / Knowledge Retrieval',
      reranking: 'Rerank Results',
      llm: 'Generate Answer',
      formatter: 'Return Documents',
      assistant: 'System Prompts',
      taskEngine: 'Task Engine',
      response: 'Response',
    };
    return names[type] || type;
  };

  const renderNodeConfig = () => {
    switch (node.data.type) {
      case 'userQuery':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <Text size="sm" c="dimmed">
                  This is where the user enters their question during the conversation.
                </Text>
              </div>

              <Divider label="Knowledge Assistant" labelPosition="center" />

              <div>
                <Switch
                  label="Enable Knowledge Assistant"
                  description="Let AI perform tasks (like writing, coding, analysis) using information from your knowledge base as context"
                  checked={
                    config?.selectedTemplate?.type === 'supervisor'
                      ? true
                      : config?.selectedTemplate?.type === 'rag'
                        ? false
                        : (localConfig.enableKnowledgeAssistant !== false)
                  }
                  onChange={(e) => setLocalConfig({ ...localConfig, enableKnowledgeAssistant: e.currentTarget.checked })}
                  size="sm"
                  disabled={config?.selectedTemplate?.type === 'supervisor' || config?.selectedTemplate?.type === 'rag'}
                  title={
                    config?.selectedTemplate?.type === 'supervisor'
                      ? 'Always enabled in Assistant mode'
                      : config?.selectedTemplate?.type === 'rag'
                        ? 'Always disabled in RAG mode - switch to Assistant Agent template to enable'
                        : ''
                  }
                />
              </div>

              {(config?.selectedTemplate?.type === 'supervisor' || localConfig.enableKnowledgeAssistant !== false) && config?.selectedTemplate?.type !== 'rag' ? (
                <div style={{
                  padding: '12px',
                  backgroundColor: 'var(--mantine-color-grape-0)',
                  border: '1px solid var(--mantine-color-grape-2)',
                  borderRadius: '6px',
                }}>
                  <Text size="xs" fw={600} c="grape.8" mb={4}>
                    🤖 Knowledge Assistant Mode
                  </Text>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      <strong>AI searches your knowledge base AND performs tasks using what it finds.</strong>
                    </Text>
                    <Text size="xs" c="dimmed">
                      <strong>How it works:</strong> Finds relevant info from your docs → Uses it to complete your task
                    </Text>
                    <Text size="xs" c="dimmed">
                      <strong>Best for:</strong> "Write a summary based on...", "Generate code using our docs", "Create a plan from..."
                    </Text>
                  </Stack>
                </div>
              ) : (
                <div style={{
                  padding: '12px',
                  backgroundColor: 'var(--mantine-color-yellow-0)',
                  border: '1px solid var(--mantine-color-yellow-2)',
                  borderRadius: '6px',
                }}>
                  <Text size="xs" fw={600} c="yellow.8" mb={4}>
                    🔍 Search-Only Mode
                  </Text>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      <strong>AI only searches and displays information from your knowledge base.</strong>
                    </Text>
                    <Text size="xs" c="dimmed">
                      <strong>Best for:</strong> "What is...?", "Find documents about...", "Show me information on..."
                    </Text>
                  </Stack>
                </div>
              )}
            </Stack>
          </div>
        );

      case 'settings':
        return (
          <div style={{ padding: '12px' }}>
            <TextInput
              label="Conversation Name"
              placeholder="My Conversation"
              value={localConfig.conversationName || ''}
              onChange={(e) => setLocalConfig({ ...localConfig, conversationName: e.currentTarget.value })}
              size="sm"
              mb="md"
              required
              withAsterisk
            />
            <Textarea
              label="Description"
              placeholder="Description of this conversation..."
              value={localConfig.conversationDescription || ''}
              onChange={(e) => setLocalConfig({ ...localConfig, conversationDescription: e.currentTarget.value })}
              rows={3}
              size="sm"
              required={localConfig.selectedStrategy !== 'native'}
              withAsterisk={localConfig.selectedStrategy !== 'native'}
            />
          </div>
        );

      case 'enhancement':
        const selectedStrategyInfo = ENHANCEMENT_STRATEGIES.find(s => s.value === (localConfig.selectedStrategy || 'native'));
        const isSupervisorMode = config?.selectedTemplate?.type === 'supervisor';

        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="sm">
              <Select
                label="Enhancement Strategy"
                data={ENHANCEMENT_STRATEGIES
                  .filter(s => isSupervisorMode ? s.value === 'custom_variants' : s.value !== 'custom_variants') // In supervisor mode, only show custom_variants. In RAG mode, show all except custom_variants
                  .map(s => ({ value: s.value, label: s.label }))}
                value={localConfig.selectedStrategy || (isSupervisorMode ? 'custom_variants' : 'native')}
                onChange={(value) => {
                  setLocalConfig({ ...localConfig, selectedStrategy: value });
                }}
                disabled={isSupervisorMode}
                size="sm"
              />

              {/* LLM Configuration - Show when non-native strategy is selected (except custom_variants in RAG mode which doesn't need LLM) */}
              {localConfig.selectedStrategy && localConfig.selectedStrategy !== 'native' && (localConfig.selectedStrategy !== 'custom_variants' || isSupervisorMode) && (
                <>
                  <Box p="xs" bg="cyan.0" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-cyan-2)' }}>
                    <Stack gap={2}>
                      <Text size="xs" fw={600} c="cyan.7">⚠️ LLM Required</Text>
                      <Text size="xs" c="dimmed">
                        {isSupervisorMode
                          ? 'The Assistant Agent requires an LLM to understand queries and execute tasks using your knowledge base as context.'
                          : 'This enhancement strategy requires an LLM to generate query variants. Select a provider and model below.'}
                      </Text>
                    </Stack>
                  </Box>

                  <Select
                    label={isSupervisorMode ? "LLM Provider (Required for Assistant)" : "LLM Provider for Query Enhancement"}
                    placeholder="Select a provider"
                    data={providers?.map((p: any) => ({
                      value: p.id,
                      label: `${p.name} (${p.provider_type})`,
                    })) || []}
                    value={localConfig.selectedProviderId}
                    onChange={(value) => setLocalConfig({ ...localConfig, selectedProviderId: value })}
                    size="sm"
                    searchable
                    clearable
                  />

                  {localConfig.selectedProviderId && providers ? (
                    <Select
                      label={isSupervisorMode ? "LLM Model (Required for Assistant)" : "Model for Query Enhancement"}
                      placeholder="Select a model"
                      data={
                        providers
                          .find((p: any) => p.id === localConfig.selectedProviderId)
                          ?.generative?.models.map((m: string) => ({
                            value: m,
                            label: m,
                          })) || []
                      }
                      value={localConfig.selectedModel}
                      onChange={(value) => setLocalConfig({ ...localConfig, selectedModel: value })}
                      size="sm"
                      searchable
                    />
                  ) : (
                    <Select
                      label={isSupervisorMode ? "LLM Model (Required for Assistant)" : "Model for Query Enhancement"}
                      placeholder="Select provider first"
                      disabled
                      size="sm"
                    />
                  )}
                </>
              )}

              {/* Custom Variants Info - Show when custom_variants is selected (in RAG mode only) */}
              {localConfig.selectedStrategy === 'custom_variants' && !isSupervisorMode && (
                <Box p="xs" bg="cyan.0" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-cyan-2)' }}>
                  <Stack gap={2}>
                    <Text size="xs" fw={600} c="cyan.7">ℹ️ Custom Variants Strategy</Text>
                    <Text size="xs" c="dimmed">
                      Use pre-defined query variants without LLM cost. The Supervisor Agent will analyze user intent and generate variants automatically.
                    </Text>
                  </Stack>
                </Box>
              )}

            </Stack>
          </div>
        );

      case 'retrieval':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Document Search (Retrieval)
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  Search documents from your knowledge base using vector similarity. Retrieved documents are passed to reranking (if enabled) or directly to answer generation.
                </Text>
              </div>

              <div>
                <Text size="xs" fw={600} mb={4} c="blue.7">What happens:</Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    1️⃣ Your query is converted to a vector embedding
                  </Text>
                  <Text size="xs" c="dimmed">
                    2️⃣ Similar documents are found using vector similarity search
                  </Text>
                  <Text size="xs" c="dimmed">
                    3️⃣ Top K most relevant documents are returned
                  </Text>
                  <Text size="xs" c="dimmed">
                    4️⃣ If using Query Enhancement (Augmented/Multi-Query/Decomposition/HyDE), results from all variants are merged using RRF
                  </Text>
                  <Text size="xs" c="dimmed">
                    5️⃣ Documents are passed to Reranking (if enabled) or Answer Generation
                  </Text>
                </Stack>
              </div>

              <Select
                label="Vector Collection *"
                data={(collections || []).map((c: any) => ({ value: c.name, label: c.name }))}
                value={localConfig.collectionName || ''}
                onChange={(value) => {
                  console.log('[Collection Select] Changed to:', value);
                  setLocalConfig({ ...localConfig, collectionName: value });
                }}
                placeholder="Select collection..."
                size="sm"
                required
                withAsterisk
                description="Choose the knowledge base to search from"
              />

              <NumberInput
                label="Top K Results *"
                value={localConfig.topK || 5}
                onChange={(value) => setLocalConfig({ ...localConfig, topK: value || 5 })}
                min={5}
                max={30}
                size="sm"
                required
                withAsterisk
                description="Number of documents to retrieve (5-30). Higher = more context but slower & more tokens"
              />

              <Box p="xs" bg="blue.0" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-blue-2)' }}>
                <Text size="xs" fw={600} mb={3} c="blue.7">💡 Tips:</Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    • Start with Top K=5 for basic needs
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Increase to 10-15 for complex queries needing more context
                  </Text>
                  <Text size="xs" c="dimmed">
                    • With Query Enhancement: The system searches ALL variants in parallel and returns your top_k best results after merging
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Use Reranking to filter irrelevant results from Top K
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Higher K + Reranking = best quality but slower and more token usage
                  </Text>
                </Stack>
              </Box>
            </Stack>
          </div>
        );

      case 'reranking':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Judge Ranker
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  When enabled, retrieved documents are evaluated and ranked before answer generation for better accuracy.
                </Text>
              </div>

              <Switch
                label="Enable Judge Ranker"
                checked={localConfig.enableReranking || false}
                onChange={(e) => {
                  setLocalConfig({
                    ...localConfig,
                    enableReranking: e.currentTarget.checked,
                    selectedRerankerId: e.currentTarget.checked ? localConfig.selectedRerankerId : null,
                    selectedRerankerModel: e.currentTarget.checked ? localConfig.selectedRerankerModel : null,
                  });
                }}
                size="sm"
                mb="md"
              />

              {/* Judge Ranker Options Hints - Same as wizard */}
              <Box p="xs" bg="white" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-gray-2)' }}>
                <Text size="xs" c="dimmed" fw={500} mb="xs">Judge Ranker Options:</Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    • <strong>Dedicated Judge:</strong> Specialized models (Cohere, Voyage AI)
                  </Text>
                  <Text size="xs" c="dimmed">
                    • <strong>LLM as Judge:</strong> Any generative LLM for evaluation
                  </Text>
                  <Text size="xs" c="dimmed">
                    • <strong>No Selection:</strong> Uses conversation's main LLM
                  </Text>
                </Stack>
              </Box>

              <Text size="xs" c="gray.6" fw={500}>
                Note: If disabled, documents go directly from retrieval to answer generation.
              </Text>

              {localConfig.enableReranking && (
                <Stack gap="md">
                  <Select
                    label="Judge Provider (Optional)"
                    data={[
                      {
                        group: 'Specialized Judges',
                        items: (providers || [])
                          .filter((p: any) => p.reranker && p.reranker.models && p.reranker.models.length > 0)
                          .map((p: any) => ({
                            value: p.id,
                            label: `${p.name} (Dedicated Judge)`,
                          })) || []
                      },
                      {
                        group: 'LLMs as Judges',
                        items: (providers || [])
                          .filter((p: any) => p.generative && p.generative.models && p.generative.models.length > 0 && (!p.reranker || !p.reranker.models || p.reranker.models.length === 0))
                          .map((p: any) => ({
                            value: p.id,
                            label: `${p.name} (LLM Judge)`,
                          })) || []
                      }
                    ]}
                    value={localConfig.selectedRerankerId || ''}
                    onChange={(value) => {
                      setLocalConfig({
                        ...localConfig,
                        selectedRerankerId: value,
                        selectedRerankerModel: null, // Reset model when provider changes
                      });
                    }}
                    placeholder="Select provider..."
                    size="sm"
                    mb="md"
                    required
                    withAsterisk
                    searchable
                    clearable
                    description="Choose a specialized judge or any LLM"
                  />

                  {localConfig.selectedRerankerId && (() => {
                    const provider = providers?.find((p: any) => p.id === localConfig.selectedRerankerId);
                    const models = provider
                      ? (provider.reranker?.models && provider.reranker.models.length > 0
                        ? provider.reranker.models
                        : provider.generative?.models || [])
                      : [];

                    return (
                      <>
                        <Text size="xs" c="dimmed">
                          {provider?.name} has {models.length} available model{models.length !== 1 ? 's' : ''}
                        </Text>
                        <Select
                          label="Judge Model"
                          data={models.map((model: string) => ({
                            value: model,
                            label: model,
                          }))}
                          value={localConfig.selectedRerankerModel || ''}
                          onChange={(value) => setLocalConfig({ ...localConfig, selectedRerankerModel: value })}
                          placeholder={models.length > 0 ? 'Select a model...' : 'No models available'}
                          disabled={!localConfig.selectedRerankerId || models.length === 0}
                          size="sm"
                          mb="md"
                          required
                          withAsterisk
                          searchable
                          clearable
                          description={`Choose the model for judging (${models.length} available)`}
                        />
                      </>
                    );
                  })()}

                  <NumberInput
                    label="Relevance Threshold"
                    description="Minimum relevance score (0.0-1.0) for filtering documents. Documents scoring below this threshold are excluded from the answer."
                    min={0}
                    max={1}
                    step={0.05}
                    value={localConfig.relevanceThreshold || 0.5}
                    onChange={(value) => setLocalConfig({ ...localConfig, relevanceThreshold: typeof value === 'number' ? value : 0.5 })}
                    placeholder="0.5"
                    size="sm"
                    mb="md"
                  />
                </Stack>
              )}
            </Stack>
          </div>
        );

      case 'llm':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Generative Answer
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  Generate natural language answers (slower, costs tokens) or show raw results (faster, exact sources)
                </Text>
              </div>

              <Switch
                label="Enable Generative Answer"
                checked={localConfig.enableLLMGeneration !== false}
                onChange={(e) => setLocalConfig({ ...localConfig, enableLLMGeneration: e.currentTarget.checked })}
                size="sm"
                mb="md"
              />

              {localConfig.enableLLMGeneration ? (
                <Stack gap="md">
                  <Select
                    label="LLM Provider"
                    data={(providers || []).map((p: any) => ({
                      value: p.id,
                      label: `${p.name} (${p.provider_type || 'LLM'})`,
                    }))}
                    value={localConfig.selectedProviderId || ''}
                    onChange={(value) => {
                      setLocalConfig({
                        ...localConfig,
                        selectedProviderId: value,
                        selectedModel: null, // Reset model when provider changes
                      });
                    }}
                    placeholder="Select provider..."
                    size="sm"
                    mb="md"
                    required
                    withAsterisk
                    searchable
                    description="Choose the LLM provider for this conversation"
                  />

                  {localConfig.selectedProviderId && (() => {
                    const provider = providers?.find((p: any) => p.id === localConfig.selectedProviderId);
                    const models = provider?.generative?.models || [];

                    return (
                      <>
                        <Text size="xs" c="dimmed">
                          {provider?.name} has {models.length} available model{models.length !== 1 ? 's' : ''}
                        </Text>
                        <Select
                          label="LLM Model"
                          data={models.map((model: string) => ({
                            value: model,
                            label: model,
                          }))}
                          value={localConfig.selectedModel || ''}
                          onChange={(value) => setLocalConfig({ ...localConfig, selectedModel: value })}
                          placeholder={models.length > 0 ? 'Select a model...' : 'No models available'}
                          disabled={!localConfig.selectedProviderId || models.length === 0}
                          size="sm"
                          mb="md"
                          required
                          withAsterisk
                          searchable
                          clearable
                          description={`Choose the LLM model for this conversation (${models.length} available)`}
                        />
                      </>
                    );
                  })()}
                </Stack>
              ) : (
                <div style={{
                  padding: '12px',
                  backgroundColor: 'var(--mantine-color-yellow-0)',
                  border: '1px solid var(--mantine-color-yellow-2)',
                  borderRadius: '6px',
                }}>
                  <Text size="xs" fw={600} c="yellow.8" mb={4}>
                    📄 Raw Results Mode
                  </Text>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      <strong>Documents displayed as-is</strong> without LLM processing
                    </Text>
                    <Text size="xs" c="dimmed">
                      <strong>Benefits:</strong> Faster responses, no token costs, 100% factual accuracy, full traceability
                    </Text>
                    <Text size="xs" c="dimmed">
                      <strong>Best for:</strong> Research, legal review, debugging, technical documentation
                    </Text>
                  </Stack>
                </div>
              )}
            </Stack>
          </div>
        );

      case 'formatter':
        return (
          <div style={{ padding: '12px', textAlign: 'center' }}>
            <Text size="sm" c="dimmed">
              Raw response mode - documents returned without LLM generation
            </Text>
          </div>
        );

      case 'assistant':
        // Tool instructions related state
        const [isInstructionsExpanded, setIsInstructionsExpanded] = useState(!!localConfig.tool_instructions);
        const [isGeneratingInstructions, setIsGeneratingInstructions] = useState(false);
        const [generationError, setGenerationError] = useState<string | null>(null);

        const selectedToolIds = localConfig.selectedTools || [];
        const selectedTools = tools ? tools.filter((t: any) => selectedToolIds.includes(t.id) && t.is_active) : [];

        // Generate tool instructions using LLM
        const generateToolInstructions = async () => {
          setIsGeneratingInstructions(true);
          setGenerationError(null);

          try {
            // Check if we have tools selected
            if (!selectedToolIds || selectedToolIds.length === 0) {
              setGenerationError('Please select at least one tool first');
              setIsGeneratingInstructions(false);
              return;
            }

            // Check if we have selected LLM provider and model from enhancement strategy
            const selectedProviderId = config.selectedProviderId;
            const selectedModel = config.selectedModel;

            if (!selectedProviderId || !selectedModel) {
              setGenerationError('Please configure LLM Provider and Model in the Query Strategy step first');
              setIsGeneratingInstructions(false);
              return;
            }

            const token = localStorage.getItem('jwt_token');
            const response = await fetch(
              apiUtils.buildApiUrl('/tools/instructions/generate'),
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                  tool_ids: selectedToolIds,
                  llm_provider_id: selectedProviderId,
                  llm_model_name: selectedModel,
                  user_context: undefined,
                }),
              }
            );

            if (!response.ok) {
              const error = await response.json();
              setGenerationError(error.detail || 'Failed to generate instructions');
              setIsGeneratingInstructions(false);
              return;
            }

            const data = await response.json();

            // Set the generated instructions
            setLocalConfig({ ...localConfig, tool_instructions: data.instructions });
            setIsInstructionsExpanded(true);

            notifications.show({
              title: 'Instructions Generated',
              message: 'Tool orchestration instructions have been generated successfully',
              color: 'green',
              icon: <IconCheck size={16} />,
            });
          } catch (error) {
            console.error('Error generating instructions:', error);
            setGenerationError(error instanceof Error ? error.message : 'Failed to generate instructions');
          } finally {
            setIsGeneratingInstructions(false);
          }
        };

        return (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Stack gap="md" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
              {/* Header */}
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Tools Selection
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  Select enabled tools that the AI agent can use to perform tasks. The agent will choose which tools to use based on the user's request.
                </Text>
              </div>

              {/* Tools List Container - Scrollable */}
              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                {toolsLoading ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                    <Text size="sm" c="dimmed">Loading tools...</Text>
                  </div>
                ) : !tools || tools.length === 0 ? (
                  <Alert icon={<IconAlertCircle size={16} />} color="yellow" variant="light">
                    <Text size="sm">No tools available. Create tools in the Tools Management section first.</Text>
                  </Alert>
                ) : (
                  <div style={{
                    flex: 1,
                    minHeight: 0,
                    overflow: 'auto',
                    paddingRight: '8px',
                    scrollBehavior: 'smooth',
                  }}>
                    <Stack gap="xs">
                      {tools.filter((t: any) => t.is_active).map((tool: any) => {
                        const isSelected = localConfig.selectedTools?.includes(tool.id) || false;
                        return (
                          <Card
                            key={tool.id}
                            withBorder
                            p="sm"
                            style={{
                              cursor: 'pointer',
                              backgroundColor: isSelected ? '#f0f4ff' : 'white',
                              borderColor: isSelected ? '#4c6ef5' : '#dee2e6',
                              borderWidth: isSelected ? '2px' : '1px',
                              transition: 'all 0.2s ease',
                            }}
                            onClick={() => {
                              const currentTools = localConfig.selectedTools || [];
                              setLocalConfig({
                                ...localConfig,
                                selectedTools: isSelected
                                  ? currentTools.filter((id: string) => id !== tool.id)
                                  : [...currentTools, tool.id]
                              });
                            }}
                          >
                            <Group align="flex-start" gap="sm">
                              {/* Checkbox */}
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                style={{
                                  marginTop: '4px',
                                  cursor: 'pointer',
                                  width: '18px',
                                  height: '18px',
                                  minWidth: '18px',
                                }}
                              />

                              {/* Tool Info */}
                              <Stack gap="xs" style={{ flex: 1 }}>
                                {/* Tool Name and Type Badge */}
                                <Group gap="xs" align="center">
                                  <Text fw={600} size="sm" c={isSelected ? 'blue.7' : 'dark'} style={{ flex: 1 }}>
                                    {tool.display_name || tool.name}
                                  </Text>
                                  <Badge
                                    size="xs"
                                    color={tool.tool_type === 'prompt_based' ? 'blue' : 'green'}
                                    variant="light"
                                  >
                                    {tool.tool_type === 'prompt_based' ? 'Prompt' : 'MCP'}
                                  </Badge>
                                </Group>

                                {/* Tool Description */}
                                {tool.description && (
                                  <Text size="xs" c="dimmed" lineClamp={2}>
                                    {tool.description}
                                  </Text>
                                )}

                                {/* Tool ID */}
                                <Text size="xs" c="gray.5" style={{ fontFamily: 'monospace' }}>
                                  {tool.name}
                                </Text>

                                {/* Tool Tags */}
                                {tool.tags && tool.tags.length > 0 && (
                                  <Group gap="xs">
                                    {tool.tags.map((tag: string) => (
                                      <Badge key={tag} size="xs" variant="dot" color="gray">
                                        {tag}
                                      </Badge>
                                    ))}
                                  </Group>
                                )}
                              </Stack>
                            </Group>
                          </Card>
                        );
                      })}
                    </Stack>
                  </div>
                )}
              </div>

              {/* Selection Summary Footer */}
              {localConfig.selectedTools && localConfig.selectedTools.length > 0 && (
                <Box
                  p="xs"
                  bg="blue.0"
                  style={{
                    borderRadius: '6px',
                    border: '1px solid var(--mantine-color-blue-2)',
                    marginTop: 'auto',
                  }}
                >
                  <Group gap="xs">
                    <IconCheck size={16} color="var(--mantine-color-blue-6)" />
                    <Text size="xs" fw={600} c="blue.7">
                      {localConfig.selectedTools.length} tool{localConfig.selectedTools.length !== 1 ? 's' : ''} selected
                    </Text>
                  </Group>
                </Box>
              )}
            </Stack>

            {/* Tool Instructions Section - Only show if tools are selected */}
            {selectedToolIds.length > 0 && (
              <Divider my="md" />
            )}

            {selectedToolIds.length > 0 && (
              <Stack gap="sm" style={{ marginTop: 'auto' }}>
                {/* Tool Instructions Card */}
                <Card withBorder p={0} style={{ overflow: 'hidden' }}>
                  {/* Header - Always visible */}
                  <Group
                    justify="space-between"
                    align="center"
                    p="sm"
                    style={{
                      cursor: 'pointer',
                      backgroundColor: isInstructionsExpanded ? 'var(--mantine-color-gray-0)' : 'transparent',
                      borderBottom: isInstructionsExpanded ? '1px solid var(--mantine-color-gray-2)' : 'none',
                    }}
                    onClick={() => setIsInstructionsExpanded(!isInstructionsExpanded)}
                  >
                    <div style={{ flex: 1 }}>
                      <Group justify="space-between" align="center" mb="xs">
                        <Text size="xs" fw={600}>
                          Tool Orchestration Instructions
                        </Text>
                        {!isInstructionsExpanded && localConfig.tool_instructions && (
                          <Text size="xs" c="dimmed">
                            {localConfig.tool_instructions.split('\n').length} line{localConfig.tool_instructions.split('\n').length !== 1 ? 's' : ''}
                          </Text>
                        )}
                      </Group>
                    </div>
                    <Group gap="xs">
                      <Button
                        size="xs"
                        variant="gradient"
                        gradient={{ from: 'cyan', to: 'blue', deg: 135 }}
                        leftSection={isGeneratingInstructions ? <Loader size={12} /> : <IconSparkles size={12} />}
                        onClick={(e) => {
                          e.stopPropagation();
                          generateToolInstructions();
                        }}
                        disabled={isGeneratingInstructions || selectedToolIds.length === 0}
                        loading={isGeneratingInstructions}
                      >
                        {isGeneratingInstructions ? 'Generating...' : 'Generate'}
                      </Button>
                      <ActionIcon
                        variant="subtle"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsInstructionsExpanded(!isInstructionsExpanded);
                        }}
                      >
                        {isInstructionsExpanded ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                      </ActionIcon>
                    </Group>
                  </Group>

                  {/* Expanded Content */}
                  {isInstructionsExpanded && (
                    <Stack spacing="sm" p="sm" pt={0}>
                      {generationError && (
                        <Alert icon={<IconAlertCircle size={14} />} color="red" variant="light" size="sm">
                          <Text size="xs">{generationError}</Text>
                        </Alert>
                      )}

                      <Textarea
                        placeholder="Describe how these tools should work together. Be specific about execution order and conditions."
                        value={localConfig.tool_instructions || ''}
                        onChange={(e) => setLocalConfig({ ...localConfig, tool_instructions: e.currentTarget.value })}
                        minRows={10}
                        styles={{
                          input: {
                            fontFamily: 'monospace',
                            fontSize: '11px',
                            minHeight: '150px',
                          },
                        }}
                      />

                      <Box p="xs" bg="yellow.0" style={{ borderRadius: '4px', border: '1px solid var(--mantine-color-yellow-2)' }}>
                        <Group gap="xs" mb="xs">
                          <IconDots size={14} />
                          <Text size="xs" fw={600}>Guidelines</Text>
                        </Group>
                        <Stack gap="xs">
                          <Text size="xs">✅ Be specific about tool execution order</Text>
                          <Text size="xs">✅ Include conditions for when to call each tool</Text>
                          <Text size="xs">✅ Describe how knowledge flows between tools</Text>
                        </Stack>
                      </Box>
                    </Stack>
                  )}
                </Card>
              </Stack>
            )}
          </div>
        );

      case 'taskEngine':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Task Engine Configuration
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  Multi-task orchestration engine that executes tasks using knowledge base search results and system prompts.
                </Text>
              </div>

              <Box p="xs" bg="violet.0" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-violet-2)' }}>
                <Text size="xs" fw={600} mb={3} c="violet.7">⚙️ Task Execution Flow:</Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    1️⃣ Receives knowledge base search results
                  </Text>
                  <Text size="xs" c="dimmed">
                    2️⃣ Applies relevant system prompts
                  </Text>
                  <Text size="xs" c="dimmed">
                    3️⃣ Orchestrates task execution across multiple agents
                  </Text>
                  <Text size="xs" c="dimmed">
                    4️⃣ Routes tasks to specialized handlers
                  </Text>
                  <Text size="xs" c="dimmed">
                    5️⃣ Synthesizes results for final response
                  </Text>
                </Stack>
              </Box>

              <Text size="xs" c="gray.6">
                Task engine automatically configured. No manual configuration needed.
              </Text>
            </Stack>
          </div>
        );

      case 'response':
        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="md">
              <div>
                <Text size="xs" fw={600} mb={4}>
                  Response Generation
                </Text>
                <Text size="xs" c="dimmed" mb="md">
                  Generates final knowledge-backed response using task engine output and retrieval results.
                </Text>
              </div>

              <Box p="xs" bg="green.0" style={{ borderRadius: '6px', border: '1px solid var(--mantine-color-green-2)' }}>
                <Text size="xs" fw={600} mb={3} c="green.7">✅ Response Features:</Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    • Grounded in knowledge base - all responses backed by KB documents
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Task results included - incorporates task engine outputs
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Traceable - can reference source documents
                  </Text>
                  <Text size="xs" c="dimmed">
                    • Synthesized - combines retrieval + task results coherently
                  </Text>
                </Stack>
              </Box>

              <Text size="xs" c="gray.6">
                Response generation automatically configured. Always references knowledge base as source of truth.
              </Text>
            </Stack>
          </div>
        );

      default:
        return (
          <div style={{ padding: '12px', textAlign: 'center' }}>
            <Text size="sm">Configuration for "{node.data.type}" is coming soon!</Text>
          </div>
        );
    }
  };

  return (
    <Paper
      shadow="xl"
      radius="md"
      style={{
        position: 'absolute',
        top: '50%',
        transform: 'translateY(-50%)',
        right: '0',
        height: 'auto',
        maxHeight: '85%',
        zIndex: 100,
        width: isExpanded ? '550px' : '50px',
        maxWidth: '90vw',
        overflow: 'hidden',
        border: '2px solid #228be6',
        borderRight: 'none',
        borderTopRightRadius: '0',
        borderBottomRightRadius: '0',
        backgroundColor: '#f8fffe',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '8px 12px',
          borderBottom: isExpanded ? '1px solid #228be6' : 'none',
          backgroundColor: '#f8fffe',
          cursor: 'pointer',
          minHeight: '44px',
          display: 'flex',
          alignItems: 'center',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <Group justify="space-between" style={{ width: '100%' }} gap="xs">
            <Group gap="xs">
              <ActionIcon
                variant="subtle"
                color="blue"
                size="xs"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
              >
                <IconChevronDown size={16} style={{ transform: 'rotate(-90deg)' }} />
              </ActionIcon>
              <Text fw={600} size="sm" c="#228be6">
                {getNodeDisplayName(node.data.type)}
              </Text>
            </Group>
            <ActionIcon
              variant="subtle"
              color="red"
              size="xs"
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
            >
              <IconX size={16} />
            </ActionIcon>
          </Group>
        ) : (
          <ActionIcon
            variant="subtle"
            color="blue"
            size="xs"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(true);
            }}
          >
            <IconChevronUp size={16} style={{ transform: 'rotate(-90deg)' }} />
          </ActionIcon>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            maxHeight: 'calc(85% - 44px)',
            overflow: 'hidden',
          }}
        >
          {/* Scrollable content area */}
          <div
            style={{
              flex: 1,
              overflow: 'auto',
              padding: '0',
              scrollBehavior: 'smooth',
            }}
          >
            {renderNodeConfig()}
          </div>

          {/* Footer with Save/Cancel buttons */}
          <Group
            justify="flex-end"
            gap="xs"
            style={{
              padding: '12px',
              borderTop: '1px solid #e0e0e0',
              backgroundColor: '#f8fffe',
              flexShrink: 0,
            }}
          >
            <Button
              variant="subtle"
              size="xs"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              color="blue"
              size="xs"
              leftSection={<IconCheck size={14} />}
              onClick={handleSave}
            >
              Save
            </Button>
          </Group>
        </div>
      )}
    </Paper>
  );
}
