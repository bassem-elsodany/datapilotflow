import {
  KnowledgeJob,
  useDeleteKnowledgeJob,
  useExecuteKnowledgeJob,
  useGetKnowledgeJobs
} from '@/api/resources/knowledge-jobs';
import { useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { JobActions } from '@/components/job-actions';
import { JobLastExecution } from '@/components/job-last-execution';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Center,
  Divider,
  Group,
  Loader,
  Modal,
  Paper,
  SegmentedControl,
  Stack,
  Text,
  ThemeIcon,
  Tooltip,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { DataTable as AppDataTable } from '@/components/data-table';
import { DataTableTable as DataTable } from '@/components/data-table/data-table-table';
import { DataTableColumn } from 'mantine-datatable';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconBriefcase,
  IconCheck,
  IconClock,
  IconFileText,
  IconPlus,
  IconRefresh,
  IconSettings,
  IconTrash,
  IconUpload,
  IconWand,
  IconX,
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { usePermissions } from '@/hooks/use-permissions';
import { useGetJobsWithStatus } from '@/hooks/api/job-status';

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

function PipelineDemoTrigger() {
  const [opened, { open, close }] = useDisclosure(false);
  return (
    <>
      <Button
        variant="light"
        color="violet"
        size="xs"
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
            <Text size="sm" fw={600}>RAG Ingestion Job Pipeline</Text>
            <Badge size="xs" variant="dot" color="green">Live</Badge>
          </Group>
        }
        size="xl"
        radius="md"
        centered
        transitionProps={{ transition: 'slide-left', duration: 400 }}
      >
        <div style={{ animation: 'slideInFromRight 0.45s cubic-bezier(0.4, 0, 0.2, 1)' }}>
          <InteractiveJobPipeline />
        </div>
      </Modal>
    </>
  );
}

function InteractiveJobPipeline() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  const steps = [
    {
      id: 'load',
      title: 'Load',
      description: 'Fetch raw content',
      details: 'The job fetches raw content from the knowledge source — web pages, uploaded files, or Confluence pages — and normalises it into a common document format ready for processing.',
      icon: IconUpload,
      color: 'blue',
      duration: 3000,
    },
    {
      id: 'parse',
      title: 'Parse',
      description: 'Extract & clean text',
      details: 'Documents are parsed to extract clean text, stripping HTML tags, boilerplate, and noise. Metadata (title, URL, author, timestamps) is preserved alongside the content.',
      icon: IconFileText,
      color: 'cyan',
      duration: 3000,
    },
    {
      id: 'chunk',
      title: 'Chunk',
      description: 'Split into segments',
      details: 'Clean text is split into overlapping chunks using the configured strategy (fixed-size, sentence, or semantic). Chunk size and overlap are tuned to maximise retrieval precision.',
      icon: IconSettings,
      color: 'orange',
      duration: 3500,
    },
    {
      id: 'embed',
      title: 'Embed',
      description: 'Generate vectors',
      details: 'Each chunk is sent to the configured embedding model (e.g. OpenAI, Cohere, local) which converts the text into a dense numerical vector capturing its semantic meaning.',
      icon: IconWand,
      color: 'violet',
      duration: 3500,
    },
    {
      id: 'store',
      title: 'Store',
      description: 'Write to vector DB',
      details: 'Chunk vectors and their metadata are upserted into the target Milvus collection. Existing documents are deduplicated by source hash to avoid re-indexing unchanged content.',
      icon: IconBriefcase,
      color: 'teal',
      duration: 3000,
    },
    {
      id: 'index',
      title: 'Index',
      description: 'Build search index',
      details: 'Milvus builds or updates its ANN (Approximate Nearest Neighbor) index on the new vectors, making them immediately queryable for RAG retrieval.',
      icon: IconCheck,
      color: 'green',
      duration: 2500,
    },
  ];

  useEffect(() => {
    if (!isPlaying) return;
    const timer = setTimeout(() => {
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        setTimeout(() => setCurrentStep(0), 1200);
      }
    }, steps[currentStep]?.duration || 3000);
    return () => clearTimeout(timer);
  }, [currentStep, isPlaying, steps]);

  return (
    <Stack gap="md">
      <Group justify="space-between" align="center">
        <Text size="xs" c="dimmed" fw={500}>
          Live walkthrough of the RAG ingestion job execution — from raw content to queryable vectors.
        </Text>
        <Button
          size="xs"
          variant="subtle"
          color={isPlaying ? 'red' : 'green'}
          leftSection={isPlaying ? <IconX size={12} /> : <IconRefresh size={12} />}
          onClick={() => setIsPlaying(p => !p)}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </Button>
      </Group>

      <Divider />

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
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '6px',
                  opacity: isActive ? 1 : 0.35,
                  transition: 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                  padding: '0 4px',
                  cursor: 'pointer',
                }}
                onClick={() => { setIsPlaying(false); setCurrentStep(index); }}
              >
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
                <Stack gap={1} style={{ textAlign: 'center', width: 80 }}>
                  <Text size="xs" fw={isCurrent ? 700 : 500} c={isCurrent ? `${step.color}.7` : 'dimmed'} style={{ transition: 'color 0.4s' }}>
                    {step.title}
                  </Text>
                  <Text size="xs" c="dimmed" lh={1.3}>{step.description}</Text>
                </Stack>
              </div>

              {index < steps.length - 1 && (
                <div style={{
                  width: 44,
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
                    width: 28,
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
                    right: 4,
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

      {steps[currentStep] && (
        <Paper withBorder p="sm" radius="sm" style={{
          borderColor: `var(--mantine-color-${steps[currentStep].color}-3)`,
          backgroundColor: `var(--mantine-color-${steps[currentStep].color}-0)`,
        }}>
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
    </Stack>
  );
}

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Processing Jobs' },
];

const statusColors: Record<string, string> = {
  created: 'cyan',
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};

export default function KnowledgeSourceJobs() {
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.innerHTML = pipelineStyles;
    document.head.appendChild(styleElement);
    return () => { document.head.removeChild(styleElement); };
  }, []);

  const navigate = useNavigate();
  const location = useLocation();
  const { hasPermission, isAdmin } = usePermissions();
  const canManage = isAdmin() || hasPermission('knowledge:manage');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<{ id: string; name: string } | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [tabValue, setTabValue] = useState<string>('*');

  const locationState = location.state as { filterConfigId?: string; filterConfigName?: string } | null;
  const [filterConfigId, setFilterConfigId] = useState<string | null>(locationState?.filterConfigId || null);

  const { data: jobs, isLoading, error, refetch } = useGetKnowledgeJobs();
  const { data: configs } = useGetKnowledgeSourceConfigs();
  const { data: jobsWithStatus } = useGetJobsWithStatus();
  const deleteJobMutation = useDeleteKnowledgeJob();
  const executeJobMutation = useExecuteKnowledgeJob();

  // Map job ID → latest execution status (from timeline data)
  const jobStatusMap = useMemo(() => {
    const map = new Map<string, string>();
    if (jobsWithStatus) {
      for (const j of jobsWithStatus) {
        if (j.current_status?.status) {
          map.set(j.id, j.current_status.status);
        }
      }
    }
    return map;
  }, [jobsWithStatus]);

  const getJobStatus = (jobId: string): string | null => jobStatusMap.get(jobId) ?? null;

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];
    if (!filterConfigId) return jobs;
    return jobs.filter(job => job.knowledge_source_config_id === filterConfigId);
  }, [jobs, filterConfigId]);

  const filteredConfigName = useMemo(() => {
    if (!filterConfigId) return null;
    return locationState?.filterConfigName || configs?.find(c => c.id === filterConfigId)?.name || 'Unknown';
  }, [filterConfigId, locationState, configs]);

  const getConfigName = (configId: string) =>
    configs?.find(c => c.id === configId)?.name || 'Unknown';

  const handleDeleteClick = (jobId: string, jobName: string) => {
    setJobToDelete({ id: jobId, name: jobName });
    setDeleteModalOpen(true);
  };

  const handleExecuteJob = async (jobId: string) => {
    try {
      await executeJobMutation.mutateAsync({ variables: {} as any, route: { jobId } });
      notifications.show({ title: 'Job Started', message: 'Job execution requested successfully', color: 'green' });
      refetch();
      setRefreshTrigger(prev => prev + 1);
    } catch {
      notifications.show({ title: 'Error', message: 'Failed to start job execution', color: 'red' });
    }
  };

  const handleDeleteConfirm = async () => {
    if (!jobToDelete) return;
    setDeletingId(jobToDelete.id);
    try {
      await deleteJobMutation.mutateAsync({ model: {}, route: { jobId: jobToDelete.id } });
      notifications.show({ title: 'Deleted', message: `"${jobToDelete.name}" deleted`, color: 'green' });
      refetch();
      setDeleteModalOpen(false);
      setJobToDelete(null);
    } catch (error: any) {
      notifications.show({ title: 'Error', message: error.message || 'Failed to delete job', color: 'red' });
    } finally {
      setDeletingId(null);
    }
  };

  const visibleJobs = filteredJobs.filter(j => {
    if (tabValue === '*') return true;
    const status = getJobStatus(j.id);
    if (tabValue === 'pending') return status === 'pending' || status === 'created';
    return status === tabValue;
  });

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

  const columns: DataTableColumn<KnowledgeJob>[] = [
    {
      accessor: 'name',
      title: 'Job',
      width: 220,
      sortable: true,
      render: (record: Record<string, unknown>) => {
        const job = record as KnowledgeJob;
        return (
          <Group gap="sm" wrap="nowrap">
            <ThemeIcon size="md" variant="light" color="blue" radius="sm" style={{ flexShrink: 0 }}>
              <IconBriefcase size={14} />
            </ThemeIcon>
            <div style={{ minWidth: 0 }}>
              <Text
                fw={600}
                size="sm"
                style={{ cursor: 'pointer', color: 'var(--mantine-color-blue-6)' }}
                truncate
                onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}
              >
                {job.name}
              </Text>
              {job.description && (
                <Text size="xs" c="dimmed" lineClamp={1}>{job.description}</Text>
              )}
            </div>
          </Group>
        );
      },
    },
    {
      accessor: 'knowledge_source_config_id',
      title: 'Configuration',
      width: 160,
      sortable: true,
      render: (record: Record<string, unknown>) => {
        const job = record as KnowledgeJob;
        return (
          <Badge
            size="sm"
            variant="light"
            color="blue"
            radius="sm"
            style={{ maxWidth: '100%', cursor: 'pointer' }}
            component={Link}
            to={paths.dashboard.management.knowledgeSources.config(job.knowledge_source_config_id)}
          >
            <Text size="xs" truncate style={{ maxWidth: 120 }}>{getConfigName(job.knowledge_source_config_id)}</Text>
          </Badge>
        );
      },
    },
    {
      accessor: 'latest_execution',
      title: 'Last Execution',
      width: 190,
      render: (record: Record<string, unknown>) => {
        const job = record as KnowledgeJob;
        return <JobLastExecution jobId={job.id} refreshTrigger={refreshTrigger} />;
      },
    },
    {
      accessor: 'created_at',
      title: 'Created',
      width: 160,
      sortable: true,
      render: (record: Record<string, unknown>) => {
        const job = record as KnowledgeJob;
        const d = new Date(job.created_at);
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
      width: 140,
      textAlign: 'right',
      render: (record: Record<string, unknown>) => {
        const job = record as KnowledgeJob;
        return (
          <JobActions
            job={job}
            onExecute={canManage ? handleExecuteJob : undefined}
            onDelete={canManage ? handleDeleteClick : undefined}
            onCancel={() => { refetch(); setRefreshTrigger(prev => prev + 1); }}
            onViewDetails={(j) => navigate(paths.dashboard.management.knowledgeSources.job(j.id))}
            isExecuting={executeJobMutation.isPending}
            isDeleting={deletingId === job.id}
          />
        );
      },
    },
  ];

  if (isLoading) {
    return (
      <Page title="Processing Jobs">
        <PageHeader title="Processing Jobs" breadcrumbs={breadcrumbs} />
        <Center h={200}><Loader size="lg" /></Center>
      </Page>
    );
  }

  if (error) {
    return (
      <Page title="Processing Jobs">
        <PageHeader title="Processing Jobs" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error">{error.message || 'Failed to load jobs'}</Alert>
      </Page>
    );
  }

  return (
    <Page title="Processing Jobs">
      <PageHeader title="Processing Jobs" breadcrumbs={breadcrumbs} />

      <AppDataTable.Container>
        <AppDataTable.Title
          title="Processing Jobs"
          description="Manage knowledge injection jobs that process data sources into searchable vector embeddings"
          actions={
            <Group gap="xs">
              {filterConfigId && (
                <Badge
                  variant="light" color="blue" size="sm"
                  rightSection={
                    <ActionIcon size="xs" variant="transparent" onClick={() => { setFilterConfigId(null); navigate(location.pathname, { replace: true, state: {} }); }}>
                      <IconX size={10} />
                    </ActionIcon>
                  }
                >
                  {filteredConfigName}
                </Badge>
              )}
              <ActionIcon variant="subtle" size="sm" onClick={() => { refetch(); setRefreshTrigger(p => p + 1); }} loading={isLoading}>
                <IconRefresh size={14} />
              </ActionIcon>
              <PipelineDemoTrigger />
              {canManage && (
                <Button
                  leftSection={<IconPlus size={14} />}
                  size="xs"
                  variant="default"
                  onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobCreate)}
                  disabled={!configs || configs.length === 0}
                >
                  New Job
                </Button>
              )}
            </Group>
          }
        />
        <AppDataTable.Tabs
          tabs={[
            { value: '*', label: 'All', counter: filteredJobs.length },
            { value: 'running', label: 'Running', color: 'blue', counter: filteredJobs.filter(j => getJobStatus(j.id) === 'running').length },
            { value: 'completed', label: 'Completed', color: 'green', counter: filteredJobs.filter(j => getJobStatus(j.id) === 'completed').length },
            { value: 'failed', label: 'Failed', color: 'red', counter: filteredJobs.filter(j => getJobStatus(j.id) === 'failed').length },
            { value: 'pending', label: 'Pending', color: 'yellow', counter: filteredJobs.filter(j => { const s = getJobStatus(j.id); return s === 'pending' || s === 'created'; }).length },
            { value: 'cancelled', label: 'Cancelled', color: 'gray', counter: filteredJobs.filter(j => getJobStatus(j.id) === 'cancelled').length },
          ]}
          onChange={setTabValue}
        />
        <AppDataTable.Content>
          <AppDataTable.Table
            records={visibleJobs}
            columns={columns}
            fetching={isLoading}
            striped
            highlightOnHover
            minHeight={200}
            noRecordsText={AppDataTable.noRecordsText('jobs')}
            recordsPerPageLabel={AppDataTable.recordsPerPageLabel('jobs')}
            paginationText={AppDataTable.paginationText('jobs')}
            page={1}
            onPageChange={() => {}}
            recordsPerPage={10}
            totalRecords={visibleJobs.length}
            onRecordsPerPageChange={() => {}}
            recordsPerPageOptions={[10, 20, 50]}
          />
        </AppDataTable.Content>
      </AppDataTable.Container>

      {/* Delete Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={() => { setDeleteModalOpen(false); setJobToDelete(null); }}
        title={
          <Group gap="xs">
            <ThemeIcon size="sm" variant="light" color="red" radius="sm"><IconTrash size={12} /></ThemeIcon>
            <Text size="sm" fw={600} c="red">Delete Job</Text>
          </Group>
        }
        centered
        size="sm"
        radius="md"
      >
        <Stack gap="md">
          <Text size="sm">
            Are you sure you want to delete <strong>"{jobToDelete?.name}"</strong>? This cannot be undone.
          </Text>
          <Group justify="flex-end" gap="xs">
            <Button variant="subtle" size="sm" onClick={() => { setDeleteModalOpen(false); setJobToDelete(null); }} disabled={deletingId !== null}>
              Cancel
            </Button>
            <Button color="red" size="sm" leftSection={<IconTrash size={14} />} onClick={handleDeleteConfirm} loading={deletingId !== null}>
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Page>
  );
}
