import {
  KnowledgeJob,
  useDeleteKnowledgeJob,
  useExecuteKnowledgeJob,
  useGetKnowledgeJobs
} from '@/api/resources/knowledge-jobs';
import {
  useGetKnowledgeSourceConfigs
} from '@/api/resources/knowledge-sources';
import { JobActions } from '@/components/job-actions';
import { JobLastExecution } from '@/components/job-last-execution';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  Alert,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconBrain,
  IconCheck,
  IconClock,
  IconCut,
  IconDatabase,
  IconFileText,
  IconPlus,
  IconRefresh,
  IconSettings,
  IconTrash,
  IconWand,
  IconWorld,
  IconX
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

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
  { label: 'Processing Jobs' },
];

const statusColors = {
  created: 'cyan',
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};


// Interactive Pipeline Component
function InteractivePipeline() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true); // Always playing by default
  const [showDetails, setShowDetails] = useState(true); // Always show details

  const steps = [
    {
      id: 'crawling',
      title: 'Crawling',
      description: 'Extract contents',
      details: 'The system crawls through configured URLs, extracting text content, metadata, and following links to discover new pages. This process respects robots.txt and rate limiting.',
      icon: IconWorld,
      color: 'blue',
      duration: 3000
    },
    {
      id: 'chunking',
      title: 'Chunking',
      description: 'Split documents into chunks',
      details: 'Large documents are intelligently split into smaller chunks using configurable size and overlap parameters. This ensures optimal processing and retrieval performance.',
      icon: IconCut,
      color: 'orange',
      duration: 2500
    },
    {
      id: 'embedding',
      title: 'Embedding',
      description: 'Generate vector representations',
      details: 'Each text chunk is converted into high-dimensional vectors using AI models. These vectors capture semantic meaning and enable similarity-based search.',
      icon: IconBrain,
      color: 'green',
      duration: 4000
    },
    {
      id: 'storage',
      title: 'Storage',
      description: 'Store vector embeddings',
      details: 'Vector embeddings are stored in the vector database with metadata, enabling fast similarity search and retrieval for RAG applications.',
      icon: IconDatabase,
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


export default function KnowledgeSourceJobs() {
  // Inject CSS animations
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = pipelineStyles;
    document.head.appendChild(styleElement);

    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  const navigate = useNavigate();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<{ id: string, name: string } | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const { data: jobs, isLoading, error, refetch } = useGetKnowledgeJobs();
  const { data: configs } = useGetKnowledgeSourceConfigs();
  const deleteJobMutation = useDeleteKnowledgeJob();
  const executeJobMutation = useExecuteKnowledgeJob();

  // Helper functions
  const getConfigName = (configId: string) => {
    const config = configs?.find(c => c.id === configId);
    return config?.name || 'Unknown Configuration';
  };


  const handleDeleteClick = (jobId: string, jobName: string) => {
    setJobToDelete({ id: jobId, name: jobName });
    setDeleteModalOpen(true);
  };

  const handleExecuteJob = async (jobId: string) => {
    try {
      await executeJobMutation.mutateAsync({
        variables: {} as any,
        route: { jobId }
      });
      notifications.show({
        title: 'Job Started',
        message: 'Job execution has been requested successfully',
        color: 'green',
      });
    } catch (error) {
      console.error('Error executing job:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to start job execution',
        color: 'red',
      });
    }
  };

  const handleDeleteConfirm = async () => {
    if (!jobToDelete) return;

    setDeletingId(jobToDelete.id);
    try {
      await deleteJobMutation.mutateAsync({
        model: {},
        route: { jobId: jobToDelete.id }
      });
      notifications.show({
        title: 'Success',
        message: `Job "${jobToDelete.name}" has been deleted successfully.`,
        color: 'green',
      });
      refetch();
      setDeleteModalOpen(false);
      setJobToDelete(null);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.message || 'Failed to delete job',
        color: 'red',
      });
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setJobToDelete(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'created':
        return <IconCheck size={16} />;
      case 'pending':
        return <IconClock size={16} />;
      case 'running':
        return <IconRefresh size={16} />;
      case 'completed':
        return <IconCheck size={16} />;
      case 'failed':
        return <IconX size={16} />;
      case 'cancelled':
        return <IconAlertCircle size={16} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    return statusColors[status as keyof typeof statusColors] || 'gray';
  };

  if (isLoading) {
    return (
      <Page title="RAG Processing Jobs">
        <PageHeader title="RAG Processing Jobs" breadcrumbs={breadcrumbs} />
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (error) {
    return (
      <Page title="RAG Processing Jobs">
        <PageHeader title="RAG Processing Jobs" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error loading jobs">
          {error.message || 'Failed to load processing jobs'}
        </Alert>
      </Page>
    );
  }

  return (
    <Page title="RAG Processing Jobs">
      <PageHeader
        title="RAG Processing Jobs"
        breadcrumbs={breadcrumbs}
      />


      <Stack gap="sm">

        <Group justify="space-between" w="100%">
          <div />
          <Group gap="sm">
            <Button
              variant="outline"
              leftSection={<IconRefresh size={16} />}
              onClick={() => {
                refetch();
                setRefreshTrigger(prev => prev + 1);
              }}
              loading={isLoading}
            >
              Refresh
            </Button>
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => navigate('/dashboard/management/knowledge-sources/job-create')}
              disabled={!configs || configs.length === 0}
            >
              Create Job
            </Button>
          </Group>
        </Group>
        <div />
      </Stack>
      <Stack gap="lg" w="100%">
        {/* Header Description */}
        <Paper withBorder p="lg" radius="md" bg="gray.0" w="100%">
          <Stack gap="md">
            <Text c="gray.6" size="sm">
              Create and manage knowledge injection jobs to process your data sources into searchable chunks.
            </Text>
            {/* Interactive Pipeline */}
            <InteractivePipeline />

            {!configs || configs.length === 0 ? (
              <Paper withBorder p="lg" radius="md" w="100%">
                <Group gap="md" align="flex-start" w="100%">
                  <ThemeIcon size={50} radius="xl" color="blue" variant="light" style={{ flexShrink: 0 }}>
                    <IconFileText size={24} />
                  </ThemeIcon>
                  <Stack gap="sm" style={{ flex: 1, minWidth: 0 }}>
                    <Title order={5} c="gray.8">No Knowledge Source Configurations</Title>
                    <Text c="gray.6" size="sm">
                      You need to create a knowledge source configuration before you can create processing jobs.
                    </Text>
                    <Button
                      leftSection={<IconFileText size={16} />}
                      onClick={() => navigate('/dashboard/management/knowledge-sources/config-create')}
                      size="sm"
                      style={{ alignSelf: 'flex-start' }}
                    >
                      Create Your First Configuration
                    </Button>
                  </Stack>
                </Group>
              </Paper>
            ) : !jobs || jobs.length === 0 ? (
              <Paper withBorder p="lg" radius="md" w="100%">
                <Group gap="md" align="flex-start" w="100%">
                  <ThemeIcon size={50} radius="xl" color="green" variant="light" style={{ flexShrink: 0 }}>
                    <IconWand size={24} />
                  </ThemeIcon>
                  <Stack gap="sm" style={{ flex: 1, minWidth: 0 }}>
                    <Title order={5} c="gray.8">No Processing Jobs Yet</Title>
                    <Text c="gray.6" size="sm">
                      Create your first knowledge processing job to start converting your data sources into searchable chunks.
                    </Text>
                    <Group gap="sm" wrap="wrap">
                      <Button
                        leftSection={<IconWand size={16} />}
                        onClick={() => navigate('/dashboard/management/knowledge-sources/job-create')}
                        size="sm"
                      >
                        Create Your First Job
                      </Button>
                      <Button
                        variant="light"
                        leftSection={<IconFileText size={16} />}
                        onClick={() => navigate('/dashboard/management/knowledge-sources/configs')}
                        size="sm"
                      >
                        View Configurations
                      </Button>
                    </Group>

                    {/* Feature highlights */}
                    <Stack gap="sm" mt="md" w="100%">
                      <Text fw={500} c="gray.7" size="xs">What you can do with processing jobs:</Text>
                      <Group gap="md" wrap="wrap" w="100%">
                        <Group gap="xs" style={{ flex: '1 1 auto', minWidth: 'fit-content' }}>
                          <ThemeIcon size={24} radius="md" color="blue" variant="light">
                            <IconBrain size={12} />
                          </ThemeIcon>
                          <Text size="xs" c="gray.6">Choose embedding models</Text>
                        </Group>
                        <Group gap="xs" style={{ flex: '1 1 auto', minWidth: 'fit-content' }}>
                          <ThemeIcon size={24} radius="md" color="orange" variant="light">
                            <IconSettings size={12} />
                          </ThemeIcon>
                          <Text size="xs" c="gray.6">Configure chunking</Text>
                        </Group>
                        <Group gap="xs" style={{ flex: '1 1 auto', minWidth: 'fit-content' }}>
                          <ThemeIcon size={24} radius="md" color="green" variant="light">
                            <IconRefresh size={12} />
                          </ThemeIcon>
                          <Text size="xs" c="gray.6">Process documents</Text>
                        </Group>
                      </Group>
                    </Stack>
                  </Stack>
                </Group>
              </Paper>
            ) : (
              <Card withBorder shadow="sm">
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Job Name</Table.Th>
                      <Table.Th>Configuration</Table.Th>
                      <Table.Th>Latest Execution</Table.Th>
                      <Table.Th>Created</Table.Th>
                      <Table.Th></Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {jobs.map((job: KnowledgeJob) => (
                      <Table.Tr key={job.id}>
                        <Table.Td>
                          <Stack gap={4}>
                            <Text
                              fw={400}
                              size="sm"
                              style={{ cursor: 'pointer', color: 'var(--mantine-color-blue-6)' }}
                              onClick={() => navigate(paths.dashboard.management.knowledgeSources.job(job.id))}
                            >
                              {job.name}
                            </Text>
                            {job.description && (
                              <Text size="sm" c="dimmed">{job.description}</Text>
                            )}
                          </Stack>
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm">{getConfigName(job.knowledge_source_config_id)}</Text>
                        </Table.Td>
                        <Table.Td>
                          <JobLastExecution jobId={job.id} refreshTrigger={refreshTrigger} />
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm" c="dimmed">
                            {(() => {
                              const date = new Date(job.created_at);
                              return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
                            })()}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <JobActions
                            job={job}
                            onExecute={handleExecuteJob}
                            onDelete={handleDeleteClick}
                            onCancel={() => {
                              refetch();
                              setRefreshTrigger(prev => prev + 1);
                            }}
                            onViewDetails={(job) => {
                              navigate(paths.dashboard.management.knowledgeSources.job(job.id));
                            }}
                            isExecuting={executeJobMutation.isPending}
                            isDeleting={deletingId === job.id}
                          />
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Card>
            )}
          </Stack>
        </Paper>
      </Stack>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={handleDeleteCancel}
        title={
          <Group gap="sm">
            <IconTrash size={20} color="var(--mantine-color-red-6)" />
            <Text fw={600} size="lg">Delete Job</Text>
          </Group>
        }
        centered
        size="md"
        radius="md"
        shadow="xl"
        transitionProps={{
          transition: 'slide-up',
          duration: 300,
          timingFunction: 'ease-out',
        }}
        overlayProps={{
          backgroundOpacity: 0.55,
          blur: 3,
          transitionProps: {
            transition: 'fade',
            duration: 300,
            timingFunction: 'ease-in-out',
          },
        }}
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-red-0)',
            borderBottom: '1px solid var(--mantine-color-red-2)',
            paddingBottom: '16px',
            marginBottom: '16px',
          },
        }}
      >
        <Stack gap="md">
          <Alert
            icon={<IconTrash size={16} />}
            title="Confirm Deletion"
            color="red"
            variant="light"
          >
            <Text>
              Are you sure you want to delete the job <strong>"{jobToDelete?.name}"</strong>?
            </Text>
          </Alert>

          <Text size="sm" c="dimmed">
            This action cannot be undone. All job data and processing results will be permanently removed.
          </Text>

          <Group justify="flex-end" gap="sm">
            <Button
              variant="light"
              onClick={handleDeleteCancel}
              disabled={deletingId !== null}
            >
              Cancel
            </Button>
            <Button
              color="red"
              onClick={handleDeleteConfirm}
              loading={deletingId !== null}
            >
              Delete Job
            </Button>
          </Group>
        </Stack>
      </Modal>

    </Page>
  );
}