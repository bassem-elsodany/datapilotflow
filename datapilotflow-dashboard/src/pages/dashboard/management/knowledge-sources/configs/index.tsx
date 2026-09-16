import { useGetKnowledgeJobs } from '@/api/resources/knowledge-jobs';
import { KnowledgeSourceConfig, useDeleteKnowledgeSourceConfig, useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Menu,
  Modal,
  Paper,
  SegmentedControl,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconBook,
  IconBookmarks,
  IconBrandHtml5,
  IconBriefcase,
  IconClock,
  IconEdit,
  IconExternalLink,
  IconFile,
  IconFileSearch,
  IconFiles,
  IconFileText,
  IconFileTypePdf,
  IconLink,
  IconMarkdown,
  IconPlus,
  IconRefresh,
  IconSettings,
  IconSitemap,
  IconTag,
  IconTrash,
  IconUpload,
  IconWand,
  IconWorld,
} from '@tabler/icons-react';
import sortBy from 'lodash/sortBy';
import { DataTable as AppDataTable } from '@/components/data-table';
import { DataTableTable as DataTable } from '@/components/data-table/data-table-table';
import { DataTableColumn, DataTableSortStatus } from 'mantine-datatable';
import { useDisclosure } from '@mantine/hooks';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePermissions } from '@/hooks/use-permissions';

// CSS animations for the pipeline
const pipelineStyles = `
  @keyframes dataFlow {
    0% { left: -10px; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { left: 50px; opacity: 0; }
  }
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }
  @keyframes arrowPulse {
    0%, 100% { transform: translateY(-50%) scale(1); }
    50% { transform: translateY(-50%) scale(1.2); }
  }
  @keyframes slideInFromRight {
    0% { transform: translateX(60px); opacity: 0; }
    100% { transform: translateX(0); opacity: 1; }
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

// Distinct icon per scraping mode
const scrapingModeIconMap: Record<string, typeof IconFileText> = {
  single_page:      IconFile,
  multiple_pages:   IconFiles,
  website:          IconSitemap,
  html_files:       IconBrandHtml5,
  markdown_files:   IconMarkdown,
  pdf_files:        IconFileTypePdf,
  docx_files:       IconFileText,
  txt_files:        IconFileText,
  space_pages:      IconBook,
  specific_pages:   IconFileSearch,
  pages_with_label: IconTag,
  recently_modified: IconClock,
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

// Trigger button that opens the pipeline demo in a slide-in modal
function PipelineDemoTrigger() {
  const [opened, { open, close }] = useDisclosure(false);
  return (
    <>
      <Button
        variant="light"
        color="violet"
        size="sm"
        leftSection={<IconWand size={14} />}
        onClick={open}
      >
        Pipeline Demo
      </Button>

      <Modal
        opened={opened}
        onClose={close}
        title={
          <Group gap="xs">
            <ThemeIcon size="sm" variant="light" color="violet" radius="sm">
              <IconWand size={12} />
            </ThemeIcon>
            <Text size="sm" fw={600}>Data Processing Pipeline</Text>
            <Badge size="xs" variant="dot" color="green">Live</Badge>
          </Group>
        }
        size="xl"
        radius="md"
        centered
        transitionProps={{ transition: 'slide-left', duration: 400 }}
      >
        <div style={{ animation: 'slideInFromRight 0.45s cubic-bezier(0.4, 0, 0.2, 1)' }}>
          <InteractiveCrawlingPipeline />
        </div>
      </Modal>
    </>
  );
}

// Interactive Crawling Pipeline Component (always fully expanded — shown inside modal)
function InteractiveCrawlingPipeline() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [showDetails, setShowDetails] = useState(true);
  const [activeDataSource, setActiveDataSource] = useState<'web_scraping' | 'local_files' | 'confluence'>('web_scraping');
  const isExpanded = true; // always open inside the modal

  // Define pipelines for each datasource type
  const pipelinesByDataSource = {
    web_scraping: [
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
    ],
    local_files: [
      {
        id: 'upload',
        title: 'Upload',
        description: 'Upload local files',
        details: 'Upload your local files (HTML, Markdown, PDF, DOCX, TXT) to be processed. The system validates file formats and prepares them for extraction.',
        icon: IconUpload,
        color: 'blue',
        duration: 2500
      },
      {
        id: 'extraction',
        title: 'Extraction',
        description: 'Extract content',
        details: 'Content is extracted from uploaded files based on their type. The system handles different file formats and converts them to a standardized format.',
        icon: IconFileText,
        color: 'orange',
        duration: 3000
      },
      {
        id: 'processing',
        title: 'Processing',
        description: 'Process and clean',
        details: 'Extracted content is cleaned, deduplicated, and processed according to your configuration. Quality checks ensure content integrity.',
        icon: IconSettings,
        color: 'green',
        duration: 2500
      },
      {
        id: 'indexing',
        title: 'Indexing',
        description: 'Index for search',
        details: 'Processed content is indexed and made available for knowledge base search and RAG operations.',
        icon: IconWand,
        color: 'purple',
        duration: 2000
      }
    ],
    confluence: [
      {
        id: 'auth',
        title: 'Authentication',
        description: 'Verify credentials',
        details: 'The system authenticates with your Confluence instance using the provided API token and validates access permissions.',
        icon: IconSettings,
        color: 'indigo',
        duration: 2500
      },
      {
        id: 'retrieval',
        title: 'Retrieval',
        description: 'Fetch pages',
        details: 'The system retrieves pages from Confluence based on your configuration - specific pages, spaces, labels, or recently modified pages.',
        icon: IconBookmarks,
        color: 'blue',
        duration: 3500
      },
      {
        id: 'conversion',
        title: 'Conversion',
        description: 'Convert to markdown',
        details: 'Confluence XHTML content is converted to markdown format, preserving structure and formatting.',
        icon: IconLink,
        color: 'orange',
        duration: 3000
      },
      {
        id: 'indexing',
        title: 'Indexing',
        description: 'Index content',
        details: 'Converted content is processed, indexed, and made available for knowledge base search and RAG operations.',
        icon: IconWand,
        color: 'green',
        duration: 2000
      }
    ]
  };

  const steps = pipelinesByDataSource[activeDataSource];

  // Auto-start the animation on component mount
  useEffect(() => {
    // Start the animation immediately when component mounts
    setCurrentStep(0);
    setShowDetails(true);
  }, []);

  // Reset animation when datasource changes
  useEffect(() => {
    setCurrentStep(0);
  }, [activeDataSource]);

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

  const sourceOptions = [
    { value: 'web_scraping', label: 'Web Scraping' },
    { value: 'local_files', label: 'Local Files' },
    { value: 'confluence', label: 'Confluence' },
  ];

  return (
    <Stack gap="md">
        {isExpanded && (
          <>
            {/* Source selector */}
            <Group gap="sm" align="center">
              <Text size="xs" c="dimmed" fw={500}>Select source type to preview its pipeline:</Text>
              <SegmentedControl
                size="xs"
                value={activeDataSource}
                onChange={(v) => setActiveDataSource(v as typeof activeDataSource)}
                data={sourceOptions}
              />
            </Group>

            <Divider />

            {/* Pipeline steps */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '6px',
              overflowX: 'auto',
              paddingBottom: '4px',
            }}>
              {steps.map((step, index) => {
                const isActive = currentStep >= index;
                const isCurrent = currentStep === index;
                const StepIcon = step.icon;

                return (
                  <div key={step.id} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '6px',
                      opacity: isActive ? 1 : 0.35,
                      transition: 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                      padding: isCurrent ? '0 4px' : '0 4px',
                    }}>
                      <ThemeIcon
                        size={isCurrent ? 40 : 32}
                        radius="xl"
                        color={step.color}
                        variant={isCurrent ? 'filled' : isActive ? 'light' : 'outline'}
                        style={{
                          flexShrink: 0,
                          overflow: 'visible',
                          transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                          boxShadow: isCurrent ? `0 0 18px var(--mantine-color-${step.color}-4)` : 'none',
                          animation: isCurrent ? 'pulse 2s infinite' : 'none',
                        }}
                      >
                        <StepIcon size={isCurrent ? 20 : 16} style={{ flexShrink: 0 }} />
                      </ThemeIcon>
                      <Stack gap={1} style={{ textAlign: 'center', width: 88 }}>
                        <Text size="xs" fw={isCurrent ? 700 : 500} c={isCurrent ? `${step.color}.7` : 'dimmed'} style={{ transition: 'color 0.4s' }}>
                          {step.title}
                        </Text>
                        <Text size="xs" c="dimmed" lh={1.3}>{step.description}</Text>
                      </Stack>
                    </div>

                    {/* Connector */}
                    {index < steps.length - 1 && (
                      <div style={{
                        width: 52,
                        height: 20,
                        flexShrink: 0,
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        opacity: isActive ? 1 : 0.2,
                        transition: 'opacity 0.5s',
                        marginBottom: 28,
                      }}>
                        <div style={{
                          width: 34,
                          height: 2,
                          background: isActive
                            ? `repeating-linear-gradient(to right, var(--mantine-color-${step.color}-4) 0px, var(--mantine-color-${step.color}-4) 4px, transparent 4px, transparent 8px)`
                            : 'var(--mantine-color-gray-3)',
                          position: 'relative',
                          overflow: 'hidden',
                          transition: 'background 0.5s',
                        }}>
                          {isCurrent && (
                            <div style={{
                              position: 'absolute',
                              top: 0,
                              left: '-10px',
                              width: 6,
                              height: 2,
                              backgroundColor: `var(--mantine-color-${step.color}-6)`,
                              borderRadius: 1,
                              animation: 'dataFlow 1.2s infinite linear',
                              boxShadow: `0 0 6px var(--mantine-color-${step.color}-4)`,
                            }} />
                          )}
                        </div>
                        <div style={{
                          position: 'absolute',
                          right: 6,
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: `6px solid ${isActive ? `var(--mantine-color-${step.color}-4)` : 'var(--mantine-color-gray-3)'}`,
                          borderTop: '4px solid transparent',
                          borderBottom: '4px solid transparent',
                          transition: 'border-color 0.5s',
                          animation: isCurrent ? 'arrowPulse 1.5s infinite' : 'none',
                        }} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Active step detail */}
            {steps[currentStep] && (
              <Paper withBorder p="sm" radius="sm" style={{ borderColor: `var(--mantine-color-${steps[currentStep].color}-3)`, backgroundColor: `var(--mantine-color-${steps[currentStep].color}-0)` }}>
                <Group gap="xs" mb={4}>
                  <ThemeIcon size="xs" color={steps[currentStep].color} variant="light" radius="xl">
                    <IconWand size={10} />
                  </ThemeIcon>
                  <Text size="xs" fw={600} c={`${steps[currentStep].color}.7`}>
                    Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
                  </Text>
                </Group>
                <Text size="xs" c="dimmed" lh={1.5}>{steps[currentStep].details}</Text>
              </Paper>
            )}
          </>
        )}
    </Stack>
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
  const { hasPermission, isAdmin } = usePermissions();
  const canManage = isAdmin() || hasPermission('knowledge:manage');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] = useState<{ id: string; name: string } | null>(null);
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus<KnowledgeSourceConfig>>({
    columnAccessor: 'created_at',
    direction: 'desc',
  });
  const [page, setPage] = useState(1);
  const [tabValue, setTabValue] = useState<string>('*');

  const { data: configsData, isLoading, error, refetch } = useGetKnowledgeSourceConfigs();
  const { data: jobsData } = useGetKnowledgeJobs();
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

  const getModeDisplay = (mode: string | undefined) => {
    if (!mode) return 'Unknown';
    switch (mode) {
      case 'website': return 'Website Crawler';
      case 'multiple_pages': return 'Multiple Pages';
      case 'single_page': return 'Single Page';
      case 'html_files': return 'HTML Files';
      case 'markdown_files': return 'Markdown Files';
      case 'pdf_files': return 'PDF Files';
      case 'docx_files': return 'DOCX Files';
      case 'txt_files': return 'TXT Files';
      case 'space_pages': return 'Space Pages';
      case 'specific_pages': return 'Specific Pages';
      case 'pages_with_label': return 'Pages w/ Label';
      case 'recently_modified': return 'Recent';
      default: return mode;
    }
  };

  const formatRelativeDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    const diff = Date.now() - date.getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 30) return `${days}d ago`;
    if (days < 365) return `${Math.floor(days / 30)}mo ago`;
    return date.toLocaleDateString();
  };

  const columns: DataTableColumn<KnowledgeSourceConfig>[] = [
    {
      accessor: 'name',
      title: 'Configuration',
      sortable: true,
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        const modeColor = (config.scraping_mode && scrapingModeColors[config.scraping_mode]) || 'gray';
        const ModeIcon = (config.scraping_mode && scrapingModeIconMap[config.scraping_mode]) || IconSettings;
        return (
          <Group gap="sm" wrap="nowrap">
            <ThemeIcon size="md" variant="light" color={modeColor} radius="sm" style={{ flexShrink: 0 }}>
              <ModeIcon size={14} />
            </ThemeIcon>
            <div style={{ minWidth: 0 }}>
              <Text
                fw={600}
                size="sm"
                component={Link}
                to={paths.dashboard.management.knowledgeSources.config(config.id)}
                c="dark"
                style={{ textDecoration: 'none' }}
              >
                {config.name}
              </Text>
              {config.description && (
                <Tooltip label={config.description} multiline maw={320} withArrow disabled={config.description.length < 60}>
                  <Text size="xs" c="dimmed" lineClamp={1}>{config.description}</Text>
                </Tooltip>
              )}
            </div>
          </Group>
        );
      },
    },
    {
      accessor: 'content_source_type',
      title: 'Source',
      width: 130,
      sortable: true,
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        const color = config.content_source_type === 'confluence' ? 'indigo' : config.content_source_type === 'local_files' ? 'violet' : 'blue';
        return (
          <Badge size="sm" variant="light" color={color} radius="sm">
            {getSourceTypeDisplay(config.content_source_type || '')}
          </Badge>
        );
      },
    },
    {
      accessor: 'scraping_mode',
      title: 'Mode',
      width: 170,
      sortable: true,
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        const color = (config.scraping_mode && scrapingModeColors[config.scraping_mode]) || 'gray';
        return (
          <Badge color={color} variant="outline" size="sm" radius="sm">
            {getModeDisplay(config.scraping_mode ?? undefined)}
          </Badge>
        );
      },
    },
    {
      accessor: 'url',
      title: 'Target',
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        let displayUrl = '';
        if (config.content_source_type === 'confluence' && config.confluence_config) {
          displayUrl = config.confluence_config.cloud_url || '—';
        } else if (config.content_source_type === 'local_files') {
          displayUrl = 'Local Storage';
        } else if (config.scraping_mode === 'multiple_pages' && config.url_source_id) {
          displayUrl = 'Multiple URLs';
        } else {
          displayUrl = config.url || '—';
        }
        return (
          <Tooltip label={displayUrl} multiline maw={300} withArrow disabled={displayUrl.length < 30}>
            <Text size="xs" c="dimmed" lineClamp={1}>{displayUrl || '—'}</Text>
          </Tooltip>
        );
      },
    },
    {
      accessor: 'jobs',
      title: 'Jobs',
      width: 80,
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        const configJobs = getJobsForConfig(config.id);
        const jobCount = configJobs.length;
        if (jobCount === 0) return <Text size="xs" c="dimmed">—</Text>;
        return (
          <Menu shadow="md" width={260} position="bottom-end">
            <Menu.Target>
              <Badge
                variant="light"
                color="violet"
                size="sm"
                radius="sm"
                style={{ cursor: 'pointer' }}
              >
                {jobCount} job{jobCount !== 1 ? 's' : ''}
              </Badge>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Related Jobs ({jobCount})</Menu.Label>
              {configJobs.map((job) => (
                <Menu.Item
                  key={job.id}
                  leftSection={<IconBriefcase size={14} />}
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}
                >
                  <Text size="sm" fw={500} lineClamp={1}>{job.name}</Text>
                </Menu.Item>
              ))}
              <Divider />
              <Menu.Item
                leftSection={<IconExternalLink size={14} />}
                onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobs, {
                  state: { filterConfigId: config.id, filterConfigName: config.name }
                })}
              >
                View All Jobs
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        );
      },
    },
    {
      accessor: 'updated_at',
      title: 'Updated',
      width: 160,
      sortable: true,
      textAlign: 'left',
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        const d = new Date(config.updated_at);
        const date = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' });
        const time = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        return (
          <Stack gap={0}>
            <Text size="xs" fw={500}>{date}</Text>
            <Text size="xs" c="dimmed">{time}</Text>
          </Stack>
        );
      },
    },
    {
      accessor: 'actions',
      title: '',
      width: 90,
      textAlign: 'right',
      toggleable: false,
      render: (record: Record<string, unknown>) => {
        const config = record as KnowledgeSourceConfig;
        return (
          <Group gap={4} justify="flex-end" wrap="nowrap">
            {canManage && (
              <Tooltip label="Edit" withArrow>
                <ActionIcon variant="subtle" color="blue" size="sm" component={Link} to={paths.dashboard.management.knowledgeSources.configEdit(config.id)}>
                  <IconEdit size={14} />
                </ActionIcon>
              </Tooltip>
            )}
            {canManage && (
              <Tooltip label="Create Job" withArrow>
                <ActionIcon
                  variant="subtle"
                  color="violet"
                  size="sm"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobCreate, {
                    state: { configId: config.id, configName: config.name }
                  })}
                >
                  <IconBriefcase size={14} />
                </ActionIcon>
              </Tooltip>
            )}
            {canManage && (
              <Tooltip label="Delete" withArrow>
                <ActionIcon variant="subtle" color="red" size="sm" onClick={() => handleDeleteClick(config.id, config.name)}>
                  <IconTrash size={14} />
                </ActionIcon>
              </Tooltip>
            )}
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

  const activeTab = tabValue ?? '*';
  const visibleConfigs = configs?.filter(c => {
    if (activeTab === '*') return true;
    return c.content_source_type === activeTab;
  }) ?? [];

  return (
    <Page title="Crawling Sources Config">
      <PageHeader title="Crawling Sources Config" breadcrumbs={breadcrumbs} />

      <AppDataTable.Container>
        <AppDataTable.Title
          title="Crawling Sources"
          description="Configure data sources to extract and index content into your knowledge base"
          actions={
            <Group gap="xs">
              <ActionIcon variant="subtle" size="sm" onClick={() => refetch()} loading={isLoading}>
                <IconRefresh size={14} />
              </ActionIcon>
              <PipelineDemoTrigger />
              {canManage && (
                <Button
                  component={Link}
                  to={paths.dashboard.management.knowledgeSources.configCreate}
                  leftSection={<IconPlus size={14} />}
                  size="xs"
                  variant="default"
                >
                  New Config
                </Button>
              )}
            </Group>
          }
        />
        <AppDataTable.Tabs
          tabs={[
            { value: '*', label: 'All', counter: configs?.length ?? 0 },
            { value: 'web_scraping', label: 'Web Scraping', color: 'blue', counter: configs?.filter(c => c.content_source_type === 'web_scraping').length ?? 0 },
            { value: 'local_files', label: 'Local Files', color: 'violet', counter: configs?.filter(c => c.content_source_type === 'local_files').length ?? 0 },
            { value: 'confluence', label: 'Confluence', color: 'indigo', counter: configs?.filter(c => c.content_source_type === 'confluence').length ?? 0 },
          ]}
          onChange={setTabValue}
        />
        <AppDataTable.Content>
          <AppDataTable.Table
            records={visibleConfigs}
            columns={columns}
            fetching={isLoading}
            striped
            highlightOnHover
            minHeight={200}
            sortStatus={sortStatus}
            onSortStatusChange={setSortStatus}
            page={page}
            onPageChange={setPage}
            recordsPerPage={10}
            totalRecords={visibleConfigs.length}
            noRecordsText={AppDataTable.noRecordsText('configurations')}
            recordsPerPageLabel={AppDataTable.recordsPerPageLabel('configurations')}
            paginationText={AppDataTable.paginationText('configurations')}
            onRecordsPerPageChange={() => {}}
            recordsPerPageOptions={[10, 20, 50]}
          />
        </AppDataTable.Content>
      </AppDataTable.Container>

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
