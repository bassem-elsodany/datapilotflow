import { useDiscoverMCPTools, useGetMCPServers } from '@/api/resources/mcp-servers';
import { PromptBasedToolConfig, useCreateTool, useGetTool, useGetTools, useUpdateTool } from '@/api/resources/tools';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  Loader,
  NumberInput,
  PasswordInput,
  Select,
  Stack,
  Switch,
  Table,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconBrain,
  IconCheck,
  IconInfoCircle,
  IconPlus,
  IconRefresh,
  IconServer,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

// System Prompt Templates
const SYSTEM_PROMPT_TEMPLATES = [
  {
    value: 'technical_assistant',
    label: '💻 Technical Assistant',
    toolName: 'technical_assistant',
    displayName: 'Technical Assistant',
    description: 'Expert software development assistant for debugging, coding, and technical problem-solving',
    prompt: `You are a highly skilled technical assistant specializing in software development and engineering.

Your capabilities:
- Analyze technical problems and provide clear solutions
- Debug code and identify issues
- Explain complex technical concepts in simple terms
- Suggest best practices and design patterns
- Help with API integration and system architecture

Guidelines:
- Always provide working, tested code examples
- Explain your reasoning step by step
- Consider edge cases and potential issues
- Reference official documentation when relevant
- Be concise but thorough in your explanations`
  },
  {
    value: 'document_reviewer',
    label: '📝 Document Reviewer',
    toolName: 'document_reviewer',
    displayName: 'Document Reviewer',
    description: 'Professional document reviewer for grammar, clarity, and content quality assessment',
    prompt: `You are an expert document reviewer with a keen eye for detail.

Your responsibilities:
- Review documents for clarity, coherence, and correctness
- Check grammar, spelling, and punctuation
- Verify factual accuracy and logical flow
- Identify inconsistencies or ambiguities
- Suggest improvements for readability and structure

Review approach:
- Provide constructive, specific feedback
- Highlight both strengths and areas for improvement
- Suggest concrete revisions when needed
- Consider the document's intended audience and purpose
- Maintain a professional, respectful tone`
  },
  {
    value: 'summarizer',
    label: '📋 Content Summarizer',
    toolName: 'content_summarizer',
    displayName: 'Content Summarizer',
    description: 'AI summarizer that extracts key points and creates concise summaries from long content',
    prompt: `You are a professional content summarizer who excels at distilling information.

Your task:
- Extract key points and main ideas from content
- Create concise, accurate summaries
- Preserve important details and context
- Organize information in a logical structure
- Identify and highlight critical insights

Summarization guidelines:
- Start with the most important information
- Use clear, simple language
- Maintain objectivity and accuracy
- Include relevant numbers, dates, and facts
- Structure summaries with bullet points or sections for readability`
  },
  {
    value: 'data_analyst',
    label: '📊 Data Analyst',
    toolName: 'data_analyst',
    displayName: 'Data Analyst',
    description: 'Data analysis expert for statistics, patterns, insights, and data-driven recommendations',
    prompt: `You are a data analyst expert who helps users understand and work with data.

Your expertise includes:
- Analyzing datasets and identifying patterns
- Creating data visualizations and reports
- Performing statistical analysis
- Generating insights from complex data
- Explaining data trends and correlations

Analysis approach:
- Ask clarifying questions about the data and objectives
- Use appropriate statistical methods
- Present findings in clear, visual formats when possible
- Provide actionable recommendations based on data
- Explain technical concepts in business-friendly language`
  },
  {
    value: 'code_reviewer',
    label: '🔍 Code Reviewer',
    toolName: 'code_reviewer',
    displayName: 'Code Reviewer',
    description: 'Expert code reviewer for quality, security, performance, and best practice assessment',
    prompt: `You are an experienced code reviewer focused on quality and best practices.

Review criteria:
- Code quality, readability, and maintainability
- Adherence to coding standards and conventions
- Security vulnerabilities and potential bugs
- Performance optimization opportunities
- Test coverage and documentation

Feedback style:
- Be specific and constructive
- Explain the "why" behind suggestions
- Prioritize issues by severity (critical, major, minor)
- Suggest concrete improvements with examples
- Recognize good practices and well-written code`
  },
  {
    value: 'business_advisor',
    label: '💼 Business Advisor',
    toolName: 'business_advisor',
    displayName: 'Business Advisor',
    description: 'Strategic business advisor for planning, analysis, and data-driven decision-making',
    prompt: `You are a strategic business advisor with expertise in operations and strategy.

Your areas of expertise:
- Business analysis and market research
- Strategic planning and decision-making
- Process improvement and optimization
- Risk assessment and mitigation
- Financial analysis and projections

Advisory approach:
- Understand business context and objectives
- Provide data-driven recommendations
- Consider both short-term and long-term implications
- Identify opportunities and potential challenges
- Offer practical, actionable advice`
  },
  {
    value: 'content_writer',
    label: '✍️ Content Writer',
    toolName: 'content_writer',
    displayName: 'Content Writer',
    description: 'Professional content writer for blogs, articles, marketing copy, and engaging content',
    prompt: `You are a skilled content writer who creates engaging, high-quality content.

Writing capabilities:
- Blog posts, articles, and marketing copy
- Technical documentation and guides
- Social media content and captions
- Email campaigns and newsletters
- Product descriptions and landing pages

Writing principles:
- Adapt tone and style to the target audience
- Use clear, compelling language
- Structure content for easy scanning and reading
- Include relevant examples and stories
- Optimize for engagement and conversion`
  },
  {
    value: 'research_assistant',
    label: '🔬 Research Assistant',
    toolName: 'research_assistant',
    displayName: 'Research Assistant',
    description: 'Comprehensive research assistant for information gathering, fact-checking, and synthesis',
    prompt: `You are a thorough research assistant who helps gather and synthesize information.

Research skills:
- Conduct comprehensive information gathering
- Verify sources and fact-check information
- Synthesize findings from multiple sources
- Identify knowledge gaps and areas for further research
- Present research in organized, accessible formats

Research methodology:
- Start with clear research questions
- Use credible, authoritative sources
- Cross-reference information for accuracy
- Provide citations and references
- Summarize complex research in digestible formats`
  },
  {
    value: 'custom',
    label: '🎨 Custom (Blank)',
    toolName: '',
    displayName: '',
    description: '',
    prompt: ''
  }
];

export default function ToolFormPage() {
  const { toolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();
  const isEditMode = !!toolId;

  const [toolType, setToolType] = useState<'prompt_based' | 'mcp_remote'>('prompt_based');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  // MCP Server Selection & Discovery State
  const [selectedMcpServerId, setSelectedMcpServerId] = useState<string>('');
  const [discoveredTools, setDiscoveredTools] = useState<any[]>([]);
  const [selectedMcpTools, setSelectedMcpTools] = useState<Set<string>>(new Set());
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [alreadyAddedToolNames, setAlreadyAddedToolNames] = useState<Set<string>>(new Set());

  const { data: existingTool, isLoading: isLoadingTool } = useGetTool(toolId!, { enabled: isEditMode });
  const { data: mcpServers, isLoading: isLoadingServers } = useGetMCPServers(true); // Only active servers
  const { data: allTools } = useGetTools(); // Fetch all tools to check for duplicates
  const createToolMutation = useCreateTool();
  const updateToolMutation = useUpdateTool();
  const discoverMCPMutation = useDiscoverMCPTools();

  const breadcrumbs = [
    { label: 'Dashboard', href: paths.dashboard.root },
    { label: 'Management', href: paths.dashboard.management.root },
    { label: 'Tools', href: paths.dashboard.management.tools.list },
    { label: isEditMode ? 'Edit' : 'Create' },
  ];

  // Form for prompt-based tools and editing
  const form = useForm({
    initialValues: {
      name: '',
      display_name: '',
      description: '',
      system_prompt: '',
      tags: [] as string[],
      is_active: true,
      // MCP fields
      server_url: '',
      tool_name: '',
      timeout: 30,
      auth_type: 'none',
      // Auth credentials
      api_key: '',
      api_key_header: 'X-API-Key',
      jwt_token: '',
      bearer_token: '',
      basic_username: '',
      basic_password: '',
    },
    validate: {
      name: (value) => (!value ? 'Tool name is required' : null),
      display_name: (value) => (!value ? 'Display name is required' : null),
      description: (value) => (!value ? 'Description is required' : null),
      system_prompt: (value, values) =>
        !isEditMode && toolType === 'prompt_based' && !value ? 'System prompt is required' : null,
    },
  });

  // Load existing tool data in edit mode
  useEffect(() => {
    if (existingTool && isEditMode) {
      setToolType(existingTool.tool_type as any);

      form.setValues({
        name: existingTool.name,
        display_name: existingTool.display_name,
        description: existingTool.description,
        is_active: existingTool.is_active,
        tags: existingTool.tags || [],
        system_prompt: existingTool.prompt_config?.system_prompt || '',
        server_url: '', // No longer used
        tool_name: existingTool.mcp_tool_name || '',
        timeout: 30,
        auth_type: 'none',
        api_key: '',
        api_key_header: 'X-API-Key',
        jwt_token: '',
        bearer_token: '',
        basic_username: '',
        basic_password: '',
      });

      // For MCP tools, load the server ID and tool name
      if (existingTool.tool_type === 'mcp_remote') {
        setSelectedMcpServerId(existingTool.mcp_server_id || '');
        // In edit mode, we don't need multiselect, just track the server
      }
    }
  }, [existingTool, isEditMode]);

  const handleSubmitPromptTool = async (values: typeof form.values) => {
    try {
      const toolData: any = {
        name: values.name,
        display_name: values.display_name,
        description: values.description,
        is_active: values.is_active,
        tags: values.tags,
      };

      if (toolType === 'prompt_based') {
        toolData.prompt_config = {
          system_prompt: values.system_prompt,
        } as PromptBasedToolConfig;
      } else {
        // For MCP tools, just send the server ID and tool name
        toolData.mcp_server_id = selectedMcpServerId;
        toolData.mcp_tool_name = values.tool_name;
      }

      if (isEditMode && toolId) {
        await updateToolMutation.mutateAsync({
          toolId,
          data: toolData,
        });
        notifications.show({
          title: 'Success',
          message: 'Tool updated successfully',
          color: 'green',
        });
      } else {
        toolData.tool_type = toolType;
        await createToolMutation.mutateAsync(toolData);
        notifications.show({
          title: 'Success',
          message: 'Tool created successfully',
          color: 'green',
        });
      }

      navigate(paths.dashboard.management.tools.list);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || `Failed to ${isEditMode ? 'update' : 'create'} tool`,
        color: 'red',
      });
    }
  };

  const handleDiscoverMCPTools = async () => {
    if (!selectedMcpServerId) {
      notifications.show({
        title: 'Error',
        message: 'Please select an MCP server',
        color: 'red',
      });
      return;
    }

    setIsDiscovering(true);
    try {
      const result = await discoverMCPMutation.mutateAsync({ serverId: selectedMcpServerId });
      
      // Find tools from this MCP server that are already added
      const existingToolsFromServer = (allTools || []).filter(
        (tool) => tool.tool_type === 'mcp_remote' && tool.mcp_server_id === selectedMcpServerId
      );
      
      const alreadyAddedNames = new Set(
        existingToolsFromServer.map((tool) => tool.mcp_tool_name || '')
      );
      
      setAlreadyAddedToolNames(alreadyAddedNames);
      
      // Filter out tools that are already added
      const newTools = result.filter((tool: any) => !alreadyAddedNames.has(tool.name));
      
      setDiscoveredTools(result); // Keep all for display, but we'll mark them

      if (result.length === 0) {
        notifications.show({
          title: 'No tools found',
          message: 'No tools were discovered on this MCP server',
          color: 'yellow',
        });
      } else if (newTools.length === 0) {
        notifications.show({
          title: 'All tools already added',
          message: `All ${result.length} discovered tool(s) from this server have already been added`,
          color: 'blue',
        });
      } else {
        const alreadyAddedCount = result.length - newTools.length;
        notifications.show({
          title: 'Success',
          message: `Discovered ${result.length} tool(s)${alreadyAddedCount > 0 ? ` (${alreadyAddedCount} already added)` : ''}`,
          color: 'green',
        });
      }
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to discover MCP tools',
        color: 'red',
      });
      setDiscoveredTools([]);
      setAlreadyAddedToolNames(new Set());
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleToggleAllMcpTools = (checked: boolean) => {
    if (checked) {
      // Only select tools that aren't already added
      const availableTools = discoveredTools
        .filter(t => !alreadyAddedToolNames.has(t.name))
        .map(t => t.name);
      setSelectedMcpTools(new Set(availableTools));
    } else {
      setSelectedMcpTools(new Set());
    }
  };

  const handleToggleMcpTool = (toolName: string) => {
    // Don't allow toggling already-added tools
    if (alreadyAddedToolNames.has(toolName)) {
      return;
    }
    
    const newSelection = new Set(selectedMcpTools);
    if (newSelection.has(toolName)) {
      newSelection.delete(toolName);
    } else {
      newSelection.add(toolName);
    }
    setSelectedMcpTools(newSelection);
  };

  const handleCreateSelectedMCPTools = async () => {
    if (selectedMcpTools.size === 0) {
      notifications.show({
        title: 'Error',
        message: 'Please select at least one tool',
        color: 'red',
      });
      return;
    }

    if (!selectedMcpServerId) {
      notifications.show({
        title: 'Error',
        message: 'No MCP server selected',
        color: 'red',
      });
      return;
    }

    const selectedToolsData = discoveredTools.filter((tool) =>
      selectedMcpTools.has(tool.name)
    );

    try {
      const promises = selectedToolsData.map((tool) => {
        const toolData = {
          name: tool.name,
          display_name: tool.display_name || tool.name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
          description: tool.description || `Tool from MCP server: ${tool.name}`,
          tool_type: 'mcp_remote' as const,
          is_active: true,
          tags: ['mcp', 'auto-discovered'],
          mcp_server_id: selectedMcpServerId,
          mcp_tool_name: tool.name,
        };

        return createToolMutation.mutateAsync(toolData);
      });

      await Promise.all(promises);

      notifications.show({
        title: 'Success',
        message: `Created ${selectedMcpTools.size} MCP tool${selectedMcpTools.size > 1 ? 's' : ''} successfully`,
        color: 'green',
      });

      navigate(paths.dashboard.management.tools.list);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to create MCP tools',
        color: 'red',
      });
    }
  };

  if (isEditMode && isLoadingTool) {
    return (
      <Page title={isEditMode ? 'Edit Tool' : 'Create Tool'}>
        <PageHeader
          title={isEditMode ? 'Edit Tool' : 'Create Tool'}
          breadcrumbs={breadcrumbs}
        />
        <Center py="xl">
          <Loader />
        </Center>
      </Page>
    );
  }

  if (isEditMode && !existingTool) {
    return (
      <Page title="Edit Tool">
        <PageHeader title="Edit Tool" breadcrumbs={breadcrumbs} />
        <Alert color="red">Tool not found</Alert>
      </Page>
    );
  }

  const pageTitle = isEditMode ? `Edit: ${existingTool?.display_name}` : 'Create New Tool';
  const pageDescription = isEditMode
    ? `Editing ${existingTool?.tool_type === 'prompt_based' ? 'Prompt-Based' : 'MCP Remote'} tool`
    : 'Create a new prompt-based tool or connect to an MCP server';

  return (
    <Page title={pageTitle}>
      <PageHeader
        title={pageTitle}
        breadcrumbs={breadcrumbs}
      />

      <Stack gap="lg">
        {/* Tool Type Selection (only in create mode) */}
        {!isEditMode && (
          <Card>
            <Stack gap="md">
              <Title order={4}>Select Tool Type</Title>
              <Select
                label="Tool Type"
                description="Choose between a prompt-based tool or MCP remote tool"
                value={toolType}
                onChange={(value) => setToolType(value as any)}
                data={[
                  { value: 'prompt_based', label: '🧠 Prompt-Based Tool' },
                  { value: 'mcp_remote', label: '🖥️ MCP Remote Tool' },
                ]}
                size="md"
              />
            </Stack>
          </Card>
        )}

        {/* Tool Configuration Form - For prompt-based tools only */}
        {toolType === 'prompt_based' && (
          <Card>
            <form onSubmit={form.onSubmit(handleSubmitPromptTool)}>
              <Stack gap="md">
                <Group justify="apart">
                  <Title order={4}>
                    {isEditMode ? 'Tool Configuration' : 'Prompt-Based Tool Configuration'}
                  </Title>
                  <IconBrain size={24} />
                </Group>

                {isEditMode && (
                  <Alert color="blue" icon={<IconInfoCircle />}>
                    Editing: <strong>{existingTool?.display_name}</strong> ({existingTool?.tool_type})
                  </Alert>
                )}

                {!isEditMode && (
                  <Alert color="blue" icon={<IconInfoCircle />}>
                    Create a tool that uses an LLM with a custom system prompt
                  </Alert>
                )}

                <Group grow align="flex-start">
                  <TextInput
                    label="Tool Name"
                    placeholder="e.g., data_analyzer"
                    description="Internal name used by the LLM (lowercase, underscores)"
                    {...form.getInputProps('name')}
                    required
                  />

                  <TextInput
                    label="Display Name"
                    placeholder="e.g., Data Analyzer"
                    description="Human-readable name for the UI"
                    {...form.getInputProps('display_name')}
                    required
                  />
                </Group>

                <Group grow align="flex-start">
                  <Textarea
                    label="Description"
                    placeholder="Describe what this tool does..."
                    description="This description helps the LLM understand when to use the tool"
                    minRows={3}
                    {...form.getInputProps('description')}
                    required
                  />

                  <TagsInput
                    label="Tags"
                    placeholder="Add tags..."
                    description="Organize your tools with tags"
                    {...form.getInputProps('tags')}
                  />
                </Group>

                {(existingTool?.tool_type === 'prompt_based' || toolType === 'prompt_based') && (
                  <>
                    {!isEditMode && (
                      <Select
                        label="System Prompt Template"
                        placeholder="Choose a template or start from scratch"
                        description="Select a pre-made template to get started quickly"
                        data={SYSTEM_PROMPT_TEMPLATES.map(t => ({ value: t.value, label: t.label }))}
                        value={selectedTemplate}
                        onChange={(value) => {
                          setSelectedTemplate(value || '');
                          const template = SYSTEM_PROMPT_TEMPLATES.find(t => t.value === value);
                          if (template) {
                            // Auto-populate all fields from template
                            form.setValues({
                              ...form.values,
                              name: template.toolName,
                              display_name: template.displayName,
                              description: template.description,
                              system_prompt: template.prompt,
                            });
                          }
                        }}
                        clearable
                        searchable
                      />
                    )}

                    <Textarea
                      label="System Prompt"
                      placeholder="You are an expert at..."
                      description="The system prompt that defines the tool's behavior"
                      minRows={3}
                      maxRows={15}
                      autosize
                      {...form.getInputProps('system_prompt')}
                      required
                    />
                  </>
                )}

                <Switch
                  label="Active"
                  description="Tool is enabled and available for use"
                  {...form.getInputProps('is_active', { type: 'checkbox' })}
                />

                <Group justify="flex-end" mt="md">
                  <Button
                    variant="subtle"
                    leftSection={<IconArrowLeft size={16} />}
                    onClick={() => navigate(paths.dashboard.management.tools.list)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    leftSection={isEditMode ? <IconCheck size={16} /> : <IconPlus size={16} />}
                    loading={createToolMutation.isPending || updateToolMutation.isPending}
                  >
                    {isEditMode ? 'Update Tool' : 'Create Tool'}
                  </Button>
                </Group>
              </Stack>
            </form>
          </Card>
        )}

        {/* MCP Remote Tool Edit Form - Only allow enable/disable */}
        {isEditMode && toolType === 'mcp_remote' && existingTool && (
          <Card>
            <Stack gap="md">
              <Group justify="apart">
                <Title order={4}>MCP Remote Tool</Title>
                <IconServer size={24} />
              </Group>

              <Alert color="yellow" icon={<IconInfoCircle />}>
                MCP remote tools are managed by their server. You can only enable/disable them here.
                To update the tool configuration, modify it on the MCP server.
              </Alert>

              {/* Readonly Tool Information */}
              <TextInput
                label="Tool Name"
                value={existingTool.name}
                readOnly
                disabled
                description="Internal name from MCP server"
              />

              <TextInput
                label="Display Name"
                value={existingTool.display_name}
                readOnly
                disabled
                description="Human-readable name"
              />

              <Textarea
                label="Description"
                value={form.values.description}
                readOnly
                disabled
                minRows={3}
                description="Tool description from MCP server"
              />

              {/* Editable Fields */}
              <TagsInput
                label="Tags"
                placeholder="Add tags..."
                description="Organize your tools with tags"
                {...form.getInputProps('tags')}
              />

              <Switch
                label="Active"
                description="Enable or disable this tool"
                {...form.getInputProps('is_active', { type: 'checkbox' })}
              />

              <Group justify="flex-end" mt="md">
                <Button
                  variant="subtle"
                  leftSection={<IconArrowLeft size={16} />}
                  onClick={() => navigate(paths.dashboard.management.tools.list)}
                >
                  Cancel
                </Button>
                <Button
                  variant="light"
                  leftSection={<IconRefresh size={16} />}
                  loading={isDiscovering}
                  onClick={async () => {
                    try {
                      setIsDiscovering(true);
                      // Reload tool descriptions from MCP server
                      const result = await discoverMCPMutation.mutateAsync({
                        serverId: existingTool.mcp_server_id!
                      });

                      // Find the current tool in the discovered list
                      const updatedTool = result.find((t: any) => t.name === existingTool.mcp_tool_name);

                      if (updatedTool) {
                        // Update form with new description
                        form.setValues({
                          ...form.values,
                          description: updatedTool.description || existingTool.description,
                        });

                        notifications.show({
                          title: 'Success',
                          message: 'Tool description reloaded from MCP server',
                          color: 'green',
                        });
                      } else {
                        notifications.show({
                          title: 'Not Found',
                          message: 'Tool not found on MCP server',
                          color: 'yellow',
                        });
                      }
                    } catch (error: any) {
                      notifications.show({
                        title: 'Error',
                        message: error.response?.data?.detail || 'Failed to reload tool description',
                        color: 'red',
                      });
                    } finally {
                      setIsDiscovering(false);
                    }
                  }}
                  disabled={isDiscovering}
                >
                  Reload Definition
                </Button>
                <Button
                  leftSection={<IconCheck size={16} />}
                  loading={updateToolMutation.isPending}
                  onClick={() => {
                    const toolData = {
                      is_active: form.values.is_active,
                      tags: form.values.tags,
                    };
                    updateToolMutation.mutateAsync({
                      toolId: toolId!,
                      data: toolData,
                    }).then(() => {
                      notifications.show({
                        title: 'Success',
                        message: 'Tool updated successfully',
                        color: 'green',
                      });
                      navigate(paths.dashboard.management.tools.list);
                    }).catch((error: any) => {
                      notifications.show({
                        title: 'Error',
                        message: error.response?.data?.detail || 'Failed to update tool',
                        color: 'red',
                      });
                    });
                  }}
                >
                  Update Tool
                </Button>
              </Group>
            </Stack>
          </Card>
        )}

        {/* MCP Remote Tool Discovery (only in create mode) */}
        {!isEditMode && toolType === 'mcp_remote' && (
          <>
            <Card>
              <Stack gap="md">
                <Group justify="apart">
                  <Title order={4}>Select MCP Server</Title>
                  <IconServer size={24} />
                </Group>

                <Alert color="blue" icon={<IconInfoCircle />}>
                  <strong>Step 1:</strong> Select an existing MCP server<br />
                  <strong>Step 2:</strong> Click "Discover Tools" to list available tools<br />
                  <strong>Step 3:</strong> Select a tool to import
                </Alert>

                {isLoadingServers ? (
                  <Center>
                    <Loader size="sm" />
                  </Center>
                ) : mcpServers && mcpServers.length > 0 ? (
                  <>
                    <Select
                      label="MCP Server"
                      placeholder="Select an MCP server"
                      description="Choose from your configured MCP servers"
                      value={selectedMcpServerId}
                      onChange={(value) => {
                        setSelectedMcpServerId(value || '');
                        setDiscoveredTools([]);
                        setSelectedMcpTools(new Set());
                        setAlreadyAddedToolNames(new Set());
                      }}
                      data={mcpServers.map(server => ({
                        value: server.id,
                        label: `${server.name} (${server.server_url})`,
                      }))}
                      required
                      searchable
                    />

                    <Group grow>
                      <Button
                        onClick={handleDiscoverMCPTools}
                        loading={isDiscovering}
                        disabled={!selectedMcpServerId}
                        leftSection={<IconServer size={16} />}
                      >
                        Discover Tools
                      </Button>
                      <Button
                        onClick={handleDiscoverMCPTools}
                        loading={isDiscovering}
                        disabled={!selectedMcpServerId || discoveredTools.length === 0}
                        variant="light"
                        leftSection={<IconRefresh size={16} />}
                        title="Reload MCP tool descriptions from server"
                      >
                        Reload
                      </Button>
                    </Group>
                  </>
                ) : (
                  <Alert color="yellow" icon={<IconAlertCircle />}>
                    No MCP servers configured. Please{' '}
                    <a href={paths.dashboard.management.mcpServers.create} style={{ textDecoration: 'underline' }}>
                      create an MCP server
                    </a>{' '}
                    first.
                  </Alert>
                )}
              </Stack>
            </Card>

            {/* Discovered Tools */}
            {discoveredTools.length > 0 && (
              <Card>
                <Stack gap="md">
                  <Group justify="space-between" align="center">
                    <Title order={4}>Discovered Tools ({discoveredTools.length})</Title>
                    {selectedMcpTools.size > 0 && (
                      <Text size="sm" c="blue" fw={500}>
                        {selectedMcpTools.size} tool{selectedMcpTools.size > 1 ? 's' : ''} selected
                      </Text>
                    )}
                  </Group>

                  <Alert color="green" icon={<IconCheck />}>
                    Select one or more tools to import into your workspace
                  </Alert>

                  <Table highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th style={{ width: '60px' }}>
                          <Checkbox
                            checked={
                              discoveredTools.filter(t => !alreadyAddedToolNames.has(t.name)).length > 0 &&
                              selectedMcpTools.size === discoveredTools.filter(t => !alreadyAddedToolNames.has(t.name)).length
                            }
                            indeterminate={
                              selectedMcpTools.size > 0 && 
                              selectedMcpTools.size < discoveredTools.filter(t => !alreadyAddedToolNames.has(t.name)).length
                            }
                            onChange={(e) => handleToggleAllMcpTools(e.currentTarget.checked)}
                          />
                        </Table.Th>
                        <Table.Th>Tool Name</Table.Th>
                        <Table.Th>Description</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {discoveredTools.map((tool) => {
                        const isAlreadyAdded = alreadyAddedToolNames.has(tool.name);
                        const isSelected = selectedMcpTools.has(tool.name);
                        
                        return (
                          <Table.Tr
                            key={tool.name}
                            style={{
                              backgroundColor: isSelected ? 'var(--mantine-color-blue-light)' : 
                                            isAlreadyAdded ? 'var(--mantine-color-gray-0)' : undefined,
                              cursor: isAlreadyAdded ? 'not-allowed' : 'pointer',
                              opacity: isAlreadyAdded ? 0.6 : 1
                            }}
                            onClick={() => handleToggleMcpTool(tool.name)}
                          >
                            <Table.Td>
                              <Checkbox
                                checked={isSelected}
                                onChange={() => handleToggleMcpTool(tool.name)}
                                onClick={(e) => e.stopPropagation()}
                                disabled={isAlreadyAdded}
                              />
                            </Table.Td>
                            <Table.Td>
                              <Group gap="xs">
                                <Text fw={isSelected ? 700 : 500} c={isAlreadyAdded ? 'dimmed' : undefined}>
                                  {tool.name}
                                </Text>
                                {isAlreadyAdded && (
                                  <Badge size="xs" color="gray" variant="light">
                                    Already Added
                                  </Badge>
                                )}
                              </Group>
                            </Table.Td>
                            <Table.Td>
                              <Text size="sm" c="dimmed">
                                {tool.description || 'No description available'}
                              </Text>
                            </Table.Td>
                          </Table.Tr>
                        );
                      })}
                    </Table.Tbody>
                  </Table>

                  <Group justify="flex-end" mt="md">
                    <Button
                      variant="subtle"
                      leftSection={<IconArrowLeft size={16} />}
                      onClick={() => navigate(paths.dashboard.management.tools.list)}
                    >
                      Cancel
                    </Button>
                    <Button
                      leftSection={<IconPlus size={16} />}
                      loading={createToolMutation.isPending}
                      disabled={selectedMcpTools.size === 0}
                      onClick={handleCreateSelectedMCPTools}
                    >
                      Add {selectedMcpTools.size > 0 ? `${selectedMcpTools.size} ` : ''}Tool{selectedMcpTools.size !== 1 ? 's' : ''}
                    </Button>
                  </Group>
                </Stack>
              </Card>
            )}
          </>
        )}
      </Stack>
    </Page>
  );
}

