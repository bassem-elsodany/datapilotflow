import { useGetKnowledgeJobs } from '@/api/resources/knowledge-jobs';
import { KnowledgeSourceConfig, useDeleteKnowledgeSourceConfig, useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Menu,
  Modal,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconBriefcase,
  IconChevronDown,
  IconEdit,
  IconExternalLink,
  IconFileText,
  IconLink,
  IconList,
  IconPlus,
  IconRefresh,
  IconSettings,
  IconTrash,
  IconUpload,
  IconWand,
  IconWorld,
  IconBookmarks
} from '@tabler/icons-react';
import sortBy from 'lodash/sortBy';
import { DataTable, DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// CSS animations for the pipeline
const pipelineStyles = `
  @keyframes dataFlow {
    0% {
      left: -10px;
      opacity: 0;
    }
    10% {
      opacity: 1;
    }
    90% {
      opacity: 1;
    }
    100% {
      left: 50px;
      opacity: 0;
    }
  }
  
  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
  }
  
  @keyframes arrowPulse {
    0%, 100% {
      transform: translateY(-50%) scale(1);
    }
    50% {
      transform: translateY(-50%) scale(1.2);
    }
  }
`;

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Crawling Sources Config' },
];


const scrapingModeIcons: Record<string, typeof IconFileText> = {
  single_page: IconFileText,
  multiple_pages: IconUpload,
  website: IconLink,
  html_files: IconFileText,
  markdown_files: IconFileText,
  pdf_files: IconFileText,
  docx_files: IconFileText,
  txt_files: IconFileText,
};

const scrapingModeColors: Record<string, string> = {
  single_page: 'blue',
  multiple_pages: 'green',
  website: 'orange',
  html_files: 'purple',
  markdown_files: 'purple',
  pdf_files: 'purple',
  docx_files: 'purple',
  txt_files: 'purple',
  space_pages: 'indigo',
  specific_pages: 'indigo',
  pages_with_label: 'indigo',
  recently_modified: 'indigo',
};

const contentSourceTypeIcons: Record<string, typeof IconFileText> = {
  web_scraping: IconWorld,
  local_files: IconFileText,
  confluence: IconBookmarks,
};

const getSourceTypeDisplay = (sourceType: string): string => {
  switch (sourceType) {
    case 'web_scraping':
      return 'Web Scraping';
    case 'local_files':
      return 'Local Files';
    case 'confluence':
      return 'Confluence';
    default:
      return sourceType;
  }
};

// Interactive Crawling Pipeline Component
function InteractiveCrawlingPipeline() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true); // Always playing by default
  const [showDetails, setShowDetails] = useState(true); // Always show details

  const steps = [
    {
      id: 'discovery',
      title: 'Discovery',
      description: 'Find and index URLs',
      details: 'The system discovers URLs from your configured sources, follows sitemaps, and builds a comprehensive list of pages to crawl. It respects robots.txt and rate limiting policies.',
      icon: IconWorld,
      color: 'blue',
      duration: 3000
    },
    {
      id: 'crawling',
      title: 'Crawling',
      description: 'Extract content from pages',
      details: 'Each discovered URL is visited to extract text content, metadata, and structure. The system handles different content types and follows links to discover new pages.',
      icon: IconLink,
      color: 'orange',
      duration: 3500
    },
    {
      id: 'filtering',
      title: 'Filtering',
      description: 'Clean and filter content',
      details: 'Extracted content is cleaned, filtered, and processed according to your configuration. Duplicates are removed and content quality is assessed.',
      icon: IconSettings,
      color: 'green',
      duration: 2500
    },
    {
      id: 'generation',
      title: 'Generation',
      description: 'Generate final content',
      details: 'Content is processed into the final format - either standard markdown with content filtering or LLM-powered markdown with intelligent processing based on your configuration.',
      icon: IconWand,
      color: 'purple',
      duration: 2000
    }
  ];

  // Auto-start the animation on component mount
  useEffect(() => {
    // Start the animation immediately when component mounts
    setCurrentStep(0);
    setShowDetails(true);
  }, []);

  useEffect(() => {
    if (!isPlaying) return;

    const timer = setTimeout(() => {
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        // Animation completed - always restart (infinite loop)
        setTimeout(() => {
          setCurrentStep(0);
        }, 1000); // 1 second pause between loops
      }
    }, steps[currentStep]?.duration || 3000);

    return () => clearTimeout(timer);
  }, [currentStep, isPlaying, steps]);

  return (
    <Card withBorder p="md" radius="md" bg="gray.0" w="100%">
      <Stack gap="sm">
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          {/* Left side - Step details */}
          <div style={{ flex: '0 0 350px', minHeight: '90px' }}>
            {isPlaying && steps[currentStep] && (
              <Alert
                icon={<IconWand size={14} />}
                title={`Processing: ${steps[currentStep].title}`}
                color={steps[currentStep].color}
                variant="light"
              >
                <Text size="xs">{steps[currentStep].details}</Text>
              </Alert>
            )}
          </div>

          {/* Right side - Pipeline */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              overflowX: 'auto',
              paddingTop: '20px',
              paddingBottom: '6px',
              minHeight: '80px'
            }}>
              {steps.map((step, index) => {
                const isActive = currentStep >= index;
                const isCurrent = currentStep === index;
                const isVisible = currentStep >= index; // Show step only when it's reached
                const StepIcon = step.icon;

                return (
                  <div key={step.id} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                    {/* Step */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                      opacity: isVisible ? 1 : 0,
                      transform: isVisible ? (isCurrent ? 'scale(1.05)' : 'scale(1)') : 'scale(0.8)',
                      transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                      animationDelay: `${index * 0.2}s`
                    }}>
                      <ThemeIcon
                        size={isCurrent ? 36 : 28}
                        radius="xl"
                        color={step.color}
                        variant={isCurrent ? "filled" : "light"}
                        style={{
                          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                          boxShadow: isCurrent ? `0 4px 20px var(--mantine-color-${step.color}-4)` : 'none',
                          animation: isCurrent ? 'pulse 2s infinite' : 'none'
                        }}
                      >
                        <StepIcon size={isCurrent ? 18 : 14} />
                      </ThemeIcon>

                      <Stack gap={1} style={{ textAlign: 'center', maxWidth: '90px' }}>
                        <Text
                          size="xs"
                          fw={isCurrent ? 600 : 500}
                          c={isCurrent ? `${step.color}.7` : "gray.8"}
                          style={{
                            transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
                          }}
                        >
                          {step.title}
                        </Text>
                        <Text size="xs" c="gray.6">
                          {step.description}
                        </Text>
                      </Stack>

                    </div>

                    {/* Connector with animated data flow */}
                    {index < steps.length - 1 && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '60px',
                        height: '20px',
                        flexShrink: 0,
                        position: 'relative',
                        opacity: isActive ? 1 : 0,
                        transform: isActive ? 'scale(1)' : 'scale(0.8)',
                        transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                        animationDelay: `${index * 0.2}s`
                      }}>
                        {/* Arrow line */}
                        <div style={{
                          width: '40px',
                          height: '2px',
                          background: isActive ? `repeating-linear-gradient(to right, var(--mantine-color-${step.color}-4) 0px, var(--mantine-color-${step.color}-4) 4px, transparent 4px, transparent 8px)` : 'repeating-linear-gradient(to right, var(--mantine-color-gray-3) 0px, var(--mantine-color-gray-3) 4px, transparent 4px, transparent 8px)',
                          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                          position: 'relative',
                          overflow: 'hidden'
                        }}>
                          {/* Animated data flow */}
                          {isCurrent && (
                            <div style={{
                              position: 'absolute',
                              top: 0,
                              left: '-10px',
                              width: '6px',
                              height: '2px',
                              backgroundColor: `var(--mantine-color-${step.color}-6)`,
                              borderRadius: '1px',
                              animation: 'dataFlow 1.5s infinite linear',
                              boxShadow: `0 0 8px var(--mantine-color-${step.color}-4)`
                            }} />
                          )}
                        </div>

                        {/* Arrow head */}
                        <div style={{
                          position: 'absolute',
                          right: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: '0',
                          height: '0',
                          borderLeft: `6px solid ${isActive ? `var(--mantine-color-${step.color}-4)` : 'var(--mantine-color-gray-3)'}`,
                          borderTop: '4px solid transparent',
                          borderBottom: '4px solid transparent',
                          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                          animation: isCurrent ? 'arrowPulse 1.5s infinite' : 'none'
                        }} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

      </Stack>
    </Card>
  );
}

export default function KnowledgeSourceConfigs() {
  // Inject CSS animations and table cell alignment
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.innerHTML = pipelineStyles + `
      /* Ensure DataTable cells are top-left aligned */
      table[data-striped] td,
      table[data-striped] th,
      .mantine-DataTable-table td,
      .mantine-DataTable-table th,
      [data-striped] td,
      [data-striped] th {
        vertical-align: top !important;
        text-align: left !important;
      }
      /* Keep Actions column right-aligned */
      table[data-striped] th:last-child,
      .mantine-DataTable-table th:last-child,
      [data-striped] th:last-child {
        text-align: right !important;
      }
      table[data-striped] td:last-child,
      .mantine-DataTable-table td:last-child,
      [data-striped] td:last-child {
        text-align: right !important;
      }
    `;
    document.head.appendChild(styleElement);
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  const navigate = useNavigate();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] = useState<{ id: string; name: string } | null>(null);
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({
    columnAccessor: 'created_at',
    direction: 'desc',
  });
  const [page, setPage] = useState(1);

  const { data: configsData, isLoading, error, refetch } = useGetKnowledgeSourceConfigs();
  const { data: jobs } = useGetKnowledgeJobs();
  const deleteConfigMutation = useDeleteKnowledgeSourceConfig();

  const [configs, setConfigs] = useState<KnowledgeSourceConfig[]>([]);

  // Helper function to get jobs for a specific config
  const getJobsForConfig = (configId: string) => {
    if (!jobs) return [];
    return jobs.filter(job => job.knowledge_source_config_id === configId);
  };

  // Helper function to count jobs per config
  const getJobCountForConfig = (configId: string) => {
    return getJobsForConfig(configId).length;
  };

  useEffect(() => {
    if (configsData) {
      const data = sortBy(configsData, sortStatus.columnAccessor) as KnowledgeSourceConfig[];
      setConfigs(sortStatus.direction === 'desc' ? data.reverse() : data);
    }
  }, [configsData, sortStatus]);

  const columns: DataTableColumn<KnowledgeSourceConfig>[] = [
      {
        accessor: 'name',
        title: 'Name',
        width: 320,
        sortable: true,
        textAlign: 'left',
        render: (record: Record<string, unknown>) => {
          const config = record as KnowledgeSourceConfig;
          const SourceIcon = (config.content_source_type && contentSourceTypeIcons[config.content_source_type]) || IconSettings;
          return (
            <Group gap="md" style={{ alignItems: 'flex-start' }}>
              <SourceIcon size={32} color="var(--mantine-color-blue-5)" style={{ flexShrink: 0, marginTop: 4 }} />
              <Stack gap={2} style={{ flex: 1 }}>
                <Text
                  fw={600}
                  size="sm"
                  component={Link}
                  to={paths.dashboard.management.knowledgeSources.config(config.id)}
                  c="dark"
                  style={{
                    textDecoration: 'none',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word',
                  }}
                  className="hover:underline"
                >
                  {config.name}
                </Text>
                <Stack gap={2}>
                  <Text size="xs" c="dimmed" fw={400}>
                    {config.content_source_type === 'confluence' ? 'Confluence' :
                     config.content_source_type === 'local_files' ? 'Local Files' :
                     'Web Scraping'}
                  </Text>
                  {config.description && (
                    <Text size="xs" c="dimmed" fw={400} lineClamp={2}>
                      {config.description}
                    </Text>
                  )}
                </Stack>
              </Stack>
            </Group>
          );
        },
      },
      {
        accessor: 'url',
        title: 'URL',
        width: 180,
        sortable: true,
        textAlign: 'left',
        render: (record: Record<string, unknown>) => {
          const config = record as KnowledgeSourceConfig;

          let displayUrl = '';
          let additionalCount = 0;

          if (config.content_source_type === 'confluence' && config.confluence_config) {
            displayUrl = config.confluence_config.cloud_url;
          } else if (config.content_source_type === 'local_files') {
            displayUrl = 'Local Storage';
          } else if (config.scraping_mode === 'multiple_pages' && config.url_source_id) {
            // For multiple_pages mode, we can show "Multiple URLs"
            displayUrl = 'Multiple URLs';
          } else {
            displayUrl = config.url || '-';
          }

          return (
            <Tooltip label={displayUrl} multiline maw={300}>
              <Text size="xs" c="dimmed" lineClamp={1} fw={400}>
                {displayUrl || '-'}
              </Text>
            </Tooltip>
          );
        },
      },
      {
        accessor: 'scraping_mode',
        title: 'Mode',
        width: 160,
        sortable: true,
        textAlign: 'left',
        render: (record: Record<string, unknown>) => {
          const config = record as KnowledgeSourceConfig;
          const getModeDisplay = (mode: string | undefined) => {
            if (!mode) return 'Unknown';
            switch (mode) {
              case 'website':
                return 'Website Crawler';
              case 'multiple_pages':
                return 'Multiple Pages';
              case 'single_page':
                return 'Single Page';
              case 'html_files':
                return 'HTML Files';
              case 'markdown_files':
                return 'Markdown Files';
              case 'pdf_files':
                return 'PDF Files';
              case 'docx_files':
                return 'DOCX Files';
              case 'txt_files':
                return 'TXT Files';
              case 'space_pages':
                return 'Space Pages';
              case 'specific_pages':
                return 'Specific Pages';
              case 'pages_with_label':
                return 'Pages with Label';
              case 'recently_modified':
                return 'Recently Modified';
              default:
                return mode;
            }
          };
          return (
            <Badge
              color={(config.scraping_mode && scrapingModeColors[config.scraping_mode]) || 'gray'}
              variant="light"
              size="sm"
            >
              {getModeDisplay(config.scraping_mode)}
            </Badge>
          );
        },
      },
      {
        accessor: 'updated_at',
        title: 'Updated',
        width: 220,
        sortable: false,
        textAlign: 'left',
        render: (record: Record<string, unknown>) => {
          const config = record as KnowledgeSourceConfig;
          const date = new Date(config.updated_at);
          const dateStr = isNaN(date.getTime()) ? 'Unknown' : date.toLocaleDateString();
          const activities = [
            dateStr,
            config.content_source_type === 'confluence' ? 'API Sync' : 'Auto Crawl',
            'Indexed'
          ];
          return (
            <Stack gap={4}>
              {activities.map((activity, idx) => (
                <Text key={idx} size="xs" c="dimmed" fw={400}>
                  {activity}
                </Text>
              ))}
            </Stack>
          );
        },
      },
      {
        accessor: 'actions',
        title: 'Actions',
        width: 180,
        textAlign: 'right',
        toggleable: false,
        render: (record: Record<string, unknown>) => {
          const config = record as KnowledgeSourceConfig;
          return (
            <Group gap="xs" justify="flex-end" style={{ alignItems: 'flex-start' }}>
              <Tooltip label="Edit Configuration">
                <ActionIcon
                  variant="subtle"
                  color="green"
                  component={Link}
                  to={paths.dashboard.management.knowledgeSources.configEdit(config.id)}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="Create Job">
                <ActionIcon
                  variant="subtle"
                  color="indigo"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobCreate, {
                    state: { configId: config.id, configName: config.name }
                  })}
                >
                  <IconBriefcase size={16} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="Delete Configuration">
                <ActionIcon
                  variant="subtle"
                  color="red"
                  onClick={() => handleDeleteClick(config.id, config.name)}
                >
                  <IconTrash size={16} />
                </ActionIcon>
              </Tooltip>
              {(() => {
                const configJobs = getJobsForConfig(config.id);
                const jobCount = configJobs.length;
                return jobCount > 0 ? (
                  <Menu shadow="md" width={250} position="bottom-end">
                    <Menu.Target>
                      <Badge
                        variant="light"
                        color="violet"
                        style={{ cursor: 'pointer', paddingLeft: 8, paddingRight: 8 }}
                      >
                        <Group gap={4}>
                          <IconList size={14} />
                          <Text size="xs">{jobCount}</Text>
                          <IconChevronDown size={12} />
                        </Group>
                      </Badge>
                    </Menu.Target>
                    <Menu.Dropdown>
                      <Menu.Label>Related Jobs ({jobCount})</Menu.Label>
                      {configJobs.map((job) => (
                        <Menu.Item
                          key={job.id}
                          leftSection={<IconBriefcase size={16} />}
                          onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}
                        >
                          <Stack gap={2}>
                            <Text size="sm" fw={500} lineClamp={1}>
                              {job.name}
                            </Text>
                            {job.description && (
                              <Text size="xs" c="dimmed" lineClamp={1}>
                                {job.description}
                              </Text>
                            )}
                          </Stack>
                        </Menu.Item>
                      ))}
                      <Divider />
                      <Menu.Item
                        leftSection={<IconExternalLink size={16} />}
                        onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs, {
                          state: { filterConfigId: config.id, filterConfigName: config.name }
                        })}
                      >
                        View All Jobs
                      </Menu.Item>
                    </Menu.Dropdown>
                  </Menu>
                ) : null;
              })()}
            </Group>
          );
        },
      },
    ];

  const handleDeleteClick = (configId: string, configName: string) => {
    // Check if the configuration still exists in the current data
    const configExists = configs?.some(config => config.id === configId);

    if (!configExists) {
      notifications.show({
        title: 'Configuration Not Found',
        message: 'This configuration may have been deleted. Refreshing the list...',
        color: 'orange',
      });
      refetch();
      return;
    }

    // Double-check: ensure we have fresh data before proceeding
    if (!configs || configs.length === 0) {
      notifications.show({
        title: 'No Data Available',
        message: 'Unable to verify configuration. Please refresh the page.',
        color: 'red',
      });
      return;
    }

    setConfigToDelete({ id: configId, name: configName });
    setDeleteModalOpen(true);
  };


  const handleDeleteConfirm = async () => {
    if (!configToDelete) return;

    // Debug: Log current configurations and the one being deleted
    console.log('Current configurations:', configs?.map(c => ({ id: c.id, name: c.name })));
    console.log('Attempting to delete:', { id: configToDelete.id, name: configToDelete.name });
    console.log('Configuration exists in current data:', configs?.some(c => c.id === configToDelete.id));

    setDeletingId(configToDelete.id);
    try {
      // Optimistic update: immediately close modal and refresh data
      setDeleteModalOpen(false);
      setConfigToDelete(null);

      await deleteConfigMutation.mutateAsync({
        model: {},
        route: { configId: configToDelete.id }
      });

      notifications.show({
        title: 'Success',
        message: 'Configuration deleted successfully',
        color: 'green',
      });

      // Force refresh to ensure data consistency
      await refetch();
    } catch (error: any) {
      let errorMessage = 'Failed to delete configuration';

      if (error.response?.status === 404) {
        errorMessage = 'Configuration not found. It may have been deleted or no longer exists.';
        // Refresh the list to sync with backend
        refetch();
        // Don't reopen modal for 404 - configuration doesn't exist
      } else if (error.response?.status === 409) {
        // Dependency conflict - show backend error message
        errorMessage = error.detail || error.response?.data?.detail || error.response?.data?.message || 'Cannot delete configuration with existing jobs. Delete related jobs first.';
        // Don't reopen modal for 409 - user needs to delete jobs first
      } else {
        // For other errors, reopen the modal so user can try again
        setConfigToDelete({ id: configToDelete.id, name: configToDelete.name });
        setDeleteModalOpen(true);

        if (error.response?.status === 403) {
          errorMessage = 'You do not have permission to delete this configuration.';
        } else if (error.response?.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (error.message) {
          errorMessage = error.message;
        }
      }

      notifications.show({
        title: 'Error',
        message: errorMessage,
        color: 'red',
      });
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setConfigToDelete(null);
  };

  if (isLoading) {
    return (
      <Page title="Crawling Sources Config">
        <PageHeader title="Crawling Sources Config" breadcrumbs={breadcrumbs} />
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (error) {
    return (
      <Page title="Crawling Sources Config">
        <PageHeader title="Crawling Sources Config" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error loading configurations">
          {error.message || 'Failed to load configurations'}
        </Alert>
      </Page>
    );
  }

  return (
    <Page title="Crawling Sources Config">
      <PageHeader
        title="Crawling Sources Config"
        breadcrumbs={breadcrumbs}
      />

      <Group justify="space-between" mb="md">
        <div />
        <Group gap="sm">
          <Button
            variant="outline"
            onClick={() => refetch()}
            leftSection={<IconRefresh size={16} />}
            loading={isLoading}
          >
            Refresh
          </Button>
          <Button
            component={Link}
            to={paths.dashboard.management.knowledgeSources.configCreate}
            leftSection={<IconPlus size={16} />}
          >
            Create Configuration
          </Button>
        </Group>
      </Group>

      <Card mb="md">
        <Stack gap="md">
          <Stack gap="sm">
            <Text size="sm" c="dimmed">
              Configure crawling sources to automatically extract and index content from websites, documents, and other data sources.
              These configurations define how the system should crawl, scrape, and process content for your knowledge base.
            </Text>
          </Stack>

          {/* Interactive Crawling Pipeline */}
          <InteractiveCrawlingPipeline />

          {!configs || configs.length === 0 ? (
            <Card>
              <Stack align="center" gap="md" py="xl">
                <IconSettings size={48} color="var(--mantine-color-dimmed)" />
                <Text size="lg" fw={500} c="dimmed">
                  No configurations found
                </Text>
                <Text size="sm" c="dimmed" ta="center">
                  Create your first knowledge source configuration to start processing documents
                </Text>
                <Button
                  component={Link}
                  to={paths.dashboard.management.knowledgeSources.configCreate}
                  leftSection={<IconPlus size={16} />}
                >
                  Create Configuration
                </Button>
              </Stack>
            </Card>
          ) : (
            <DataTable
              records={configs}
              columns={columns}
              striped
              highlightOnHover
              minHeight={200}
              sortStatus={sortStatus}
              onSortStatusChange={setSortStatus}
              page={page}
              onPageChange={setPage}
              recordsPerPage={10}
              totalRecords={configs.length}
              paginationSize="sm"
              borderRadius="sm"
              shadow="sm"
              withTableBorder
              styles={{
                td: {
                  verticalAlign: 'top',
                  textAlign: 'left',
                },
                th: {
                  verticalAlign: 'top',
                  textAlign: 'left',
                },
              }}
            />
          )}
        </Stack>
      </Card>

      {/* Delete Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title={
          <Group gap="sm">
            <IconTrash size={20} color="var(--mantine-color-red-6)" />
            <Title order={5} c="red">Delete Configuration</Title>
          </Group>
        }
        centered
        size="md"
        radius="md"
        shadow="xl"
        styles={{
          content: {
            animation: 'slideUp 0.3s ease-out',
          },
          header: {
            borderBottom: '1px solid var(--mantine-color-gray-3)',
            paddingBottom: 'var(--mantine-spacing-md)',
          },
        }}
      >
        <Stack gap="md">
          <Alert
            icon={<IconAlertTriangle size={16} />}
            title="Are you sure?"
            color="red"
            variant="light"
            radius="md"
          >
            This action cannot be undone. The configuration <strong>{configToDelete?.name}</strong> will be permanently deleted.
          </Alert>

          <Text size="sm" c="dimmed">
            This will remove all associated data and cannot be recovered.
          </Text>

          <Group justify="flex-end" gap="sm" mt="md">
            <Button
              variant="outline"
              color="gray"
              onClick={() => setDeleteModalOpen(false)}
              style={{
                transition: 'all 0.2s ease-in-out',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              Cancel
            </Button>
            <Button
              color="red"
              loading={deletingId === configToDelete?.id}
              onClick={handleDeleteConfirm}
              radius="md"
              leftSection={<IconTrash size={16} />}
              style={{
                transition: 'all 0.2s ease-in-out',
              }}
              onMouseEnter={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(220, 38, 38, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              Delete Configuration
            </Button>
          </Group>
        </Stack>
      </Modal>

    </Page>
  );
}
