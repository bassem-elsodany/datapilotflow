/**
 * Conversation Node Configuration Panel
 *
 * Right-side panel for configuring conversation pipeline nodes
 * EXACTLY SAME as job pipeline's NodeConfigPanel
 */

import { ActionIcon, Group, Select, NumberInput, Switch, TextInput, Textarea, Paper, Text, Stack, Badge, Box, List, Divider, Button } from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconX, IconHelp, IconCheck, IconAlertCircle } from '@tabler/icons-react';
import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { notifications } from '@mantine/notifications';

interface ConversationNodeData {
  id: string;
  name: string;
  type: 'userQuery' | 'settings' | 'enhancement' | 'retrieval' | 'reranking' | 'llm' | 'formatter';
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

  useEffect(() => {
    if (opened && node) {
      setIsExpanded(true);
      setLocalConfig(config);
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

    onSave(node.id, localConfig);
    onClose();
  };

  const getNodeDisplayName = (type: string): string => {
    const names: Record<string, string> = {
      userQuery: 'User Query',
      settings: 'Conversation Settings',
      enhancement: 'Query Strategy',
      retrieval: 'Document Search',
      reranking: 'Rerank Results',
      llm: 'Generate Answer',
      formatter: 'Return Documents',
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
                  checked={localConfig.enableKnowledgeAssistant !== false}
                  onChange={(e) => setLocalConfig({ ...localConfig, enableKnowledgeAssistant: e.currentTarget.checked })}
                  size="sm"
                />
              </div>

              {localConfig.enableKnowledgeAssistant !== false ? (
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

        return (
          <div style={{ padding: '12px' }}>
            <Stack gap="sm">
              <Select
                label="Enhancement Strategy"
                data={ENHANCEMENT_STRATEGIES.map(s => ({ value: s.value, label: s.label }))}
                value={localConfig.selectedStrategy || 'native'}
                onChange={(value) => setLocalConfig({ ...localConfig, selectedStrategy: value })}
                size="sm"
              />

              {/* Strategy Information Card */}
              {selectedStrategyInfo && (
                <Box p="sm" style={{
                  backgroundColor: `var(--mantine-color-${selectedStrategyInfo.color}-0)`,
                  border: `1px solid var(--mantine-color-${selectedStrategyInfo.color}-2)`,
                  borderRadius: '6px',
                }}>
                  <Stack gap="xs">
                    {/* Description */}
                    <Text size="xs" c="dimmed">
                      {selectedStrategyInfo.details}
                    </Text>

                    <Divider />

                    {/* Pros and Cons in columns */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                    }}>
                      <div>
                        <Text size="xs" fw={600} c={`${selectedStrategyInfo.color}.7`} mb={4}>
                          ✓ Pros
                        </Text>
                        <Stack gap={2}>
                          {selectedStrategyInfo.pros.map((pro, idx) => (
                            <Text key={idx} size="xs" c="dimmed">
                              • {pro}
                            </Text>
                          ))}
                        </Stack>
                      </div>
                      <div>
                        <Text size="xs" fw={600} c="red.7" mb={4}>
                          ✗ Cons
                        </Text>
                        <Stack gap={2}>
                          {selectedStrategyInfo.cons.map((con, idx) => (
                            <Text key={idx} size="xs" c="dimmed">
                              • {con}
                            </Text>
                          ))}
                        </Stack>
                      </div>
                    </div>

                    {/* Best For Use Cases */}
                    <div>
                      <Text size="xs" fw={600} c="blue.7" mb={4}>
                        Best For
                      </Text>
                      <Group gap={4}>
                        {selectedStrategyInfo.useCases.map((useCase, idx) => (
                          <Badge key={idx} size="xs" variant="dot" color={selectedStrategyInfo.color}>
                            {useCase}
                          </Badge>
                        ))}
                      </Group>
                    </div>

                    {/* Example Section */}
                    {selectedStrategyInfo.example && (
                      <>
                        <Divider />
                        <div>
                          <Text size="xs" fw={600} c="violet.7" mb={4}>
                            📝 Example
                          </Text>
                          <Box p="xs" bg="white" style={{ borderRadius: '4px', border: `1px solid var(--mantine-color-${selectedStrategyInfo.color}-2)` }}>
                            <Stack gap="xs">
                              <div>
                                <Text size="xs" c="dimmed" fw={500} mb={2}>Original Query:</Text>
                                <Text size="xs" fw={500}>{selectedStrategyInfo.example.original}</Text>
                              </div>
                              <Divider />
                              <div>
                                <Text size="xs" c="dimmed" fw={500} mb={2}>Strategy Output:</Text>
                                <Text size="xs" style={{ whiteSpace: 'pre-line' }}>{selectedStrategyInfo.example.output}</Text>
                              </div>
                            </Stack>
                          </Box>
                        </div>
                      </>
                    )}
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
                onChange={(value) => setLocalConfig({ ...localConfig, collectionName: value })}
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
        maxHeight: '80vh',
        zIndex: 100,
        width: isExpanded ? '420px' : '50px',
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
            maxHeight: 'calc(80vh - 44px)',
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
