import { useJobTimelineEntries, useJobTimelineStatistics } from '@/api/resources/job-timelines';
import { useGetKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { useGetKnowledgeSourceConfigs } from '@/api/resources/knowledge-sources';
import { useGetModelProviders } from '@/api/resources/model-providers';
import { useGetKnowledgeVectorDBCollection } from '@/api/resources/vectordb-collections';
import { InfoItem, InfoSectionCard } from '@/components/info-section-card';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { StatCard } from '@/components/stat-card';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Box,
  Button,
  Center,
  Code,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Text,
  Timeline
} from '@mantine/core';
import {
  IconAlertCircle,
  IconArrowLeft,
  IconCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconEdit,
  IconFileText,
  IconInfoCircle,
  IconPlayerPlay,
  IconRefresh,
  IconScissors,
  IconSettings,
  IconNetwork,
  IconX
} from '@tabler/icons-react';
import { Link, useParams } from 'react-router-dom';

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'RAG Configuration', href: paths.dashboard.management.knowledgeSources.root },
  { label: 'Job Details' },
];

const statusColors = {
  created: 'cyan',
  pending: 'yellow',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};

const statusIcons = {
  created: IconCheck,
  pending: IconClock,
  running: IconPlayerPlay,
  completed: IconCheck,
  failed: IconX,
  cancelled: IconAlertCircle,
};

export default function KnowledgeSourceJobDetails() {
  const { jobId } = useParams<{ jobId: string }>();

  const { data: job, isLoading, error, refetch } = useGetKnowledgeJob(jobId || '', {
    query: { expand: 'document_splitter,vectordb_collection,knowledge_source_config' }
  });
  const { data: configs } = useGetKnowledgeSourceConfigs();
  const { data: modelProviders } = useGetModelProviders();

  // Fetch VectorDB collection data - only when we have a valid collection ID
  const { data: vectordbCollection, isLoading: isLoadingCollection } = useGetKnowledgeVectorDBCollection(
    job?.vectordb_collection_id || '',
    { enabled: !!job?.vectordb_collection_id }
  );

  // Fetch job timeline entries and statistics
  const { data: timelineEntries, isLoading: isLoadingTimeline, error: timelineError } = useJobTimelineEntries(jobId || '', { limit: 10 });
  const { data: timelineStats, isLoading: isLoadingStats, error: statsError } = useJobTimelineStatistics(jobId || '');

  // Helper function to get configuration name
  const getConfigName = (configId: string) => {
    const config = configs?.find(c => c.id === configId);
    return config ? config.name : 'Unknown Configuration';
  };

  // Helper function to get model provider name
  const getProviderName = (providerId: string) => {
    const provider = modelProviders?.find(p => p.id === providerId);
    return provider ? provider.name : 'Unknown Provider';
  };

  if (isLoading || isLoadingCollection || isLoadingTimeline || isLoadingStats) {
    return (
      <Page title="Job Details">
        <PageHeader title="Job Details" breadcrumbs={breadcrumbs} />
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Page>
    );
  }

  if (error || !job) {
    return (
      <Page title="Job Details">
        <PageHeader title="Job Details" breadcrumbs={breadcrumbs} />
        <Alert color="red" title="Error loading job">
          {error?.message || 'Job not found'}
        </Alert>
      </Page>
    );
  }

  const getStatusDescription = (status: string) => {
    switch (status) {
      case 'created':
        return 'Job has been created and is ready to be processed';
      case 'pending':
        return 'Job is waiting to be processed';
      case 'running':
        return 'Job is currently being processed';
      case 'completed':
        return 'Job has completed successfully';
      case 'failed':
        return 'Job failed during processing';
      case 'cancelled':
        return 'Job was cancelled';
      default:
        return 'Unknown status';
    }
  };

  // Get the latest status from timeline entries, default to 'created' if no entries exist
  const latestStatus = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0].status : 'created';
  const StatusIcon = statusIcons[latestStatus];

  // Check if timeline data is available (not 404 error)
  const hasTimelineData = timelineEntries !== undefined && !timelineError;
  const hasStatsData = timelineStats !== undefined && !statsError;

  // Create timeline items from job timeline entries
  const timelineItems = timelineEntries?.map((entry, index) => ({
    title: `Execution #${timelineEntries.length - index}`,
    description: `${entry.status} - ${entry.documents_processed} docs, ${entry.chunks_created} chunks`,
    icon: statusIcons[entry.status],
    color: statusColors[entry.status],
    entry: entry,
  })) || [];

  return (
    <Page title="Job Details">
      <PageHeader
        title="Job Details"
        breadcrumbs={breadcrumbs}
      />

      <Group justify="space-between" mb="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          component={Link}
          to={paths.dashboard.management.knowledgeSources.jobs}
        >
          Back to Jobs
        </Button>
        <Group>
          <Button
            variant="filled"
            leftSection={<IconEdit size={16} />}
            component={Link}
            to={`/dashboard/management/knowledge-sources/job-edit/${jobId}`}
          >
            Edit Job
          </Button>
          <Button
            variant="subtle"
            leftSection={<IconRefresh size={16} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </Group>
      </Group>

      <Stack gap="xl">
        {/* Job Header with Status */}
        <Box
          style={{
            background: `linear-gradient(135deg, #45c9bb15 0%, #87cbbc20 100%)`,
            border: '1px solid #45c9bb30',
            borderRadius: '16px',
            padding: '20px',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <Box
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(90deg, #45c9bb 0%, #87cbbc 100%)'
            }}
          />
          <Group justify="space-between" align="flex-start">
            <Stack gap="xs">
              <Text size="24px" fw={700} style={{ color: '#45c9bb' }}>
                {job.name}
              </Text>
              {job.description && (
                <Text size="sm" c="dimmed" style={{ maxWidth: '600px' }}>
                  {job.description}
                </Text>
              )}
              <Group gap="sm" mt={4}>
                <Badge leftSection={<StatusIcon size={12} />} color={statusColors[latestStatus]} size="sm" variant="light">
                  {latestStatus}
                </Badge>
                <Text size="xs" c="dimmed">
                  {getStatusDescription(latestStatus)}
                </Text>
              </Group>
            </Stack>
          </Group>
        </Box>

        {/* Stats Cards */}
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg">
          <Link
            to={`/dashboard/management/knowledge-sources/configs/${job.knowledge_source_config_id}`}
            style={{ textDecoration: 'none', display: 'block' }}
          >
            <Box style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
              sx={{ '&:hover': { transform: 'translateY(-2px)' } }}>
              <StatCard
                title="Configuration"
                value={getConfigName(job.knowledge_source_config_id)}
                icon={<IconSettings size={24} />}
                color="#45c9bb"
                gradientFrom="#45c9bb"
                gradientTo="#87cbbc"
                description="Click to view details"
              />
            </Box>
          </Link>
          <StatCard
            title="Documents Processed"
            value={timelineEntries && timelineEntries.length > 0 ? timelineEntries[0].documents_processed : 0}
            icon={<IconFileText size={24} />}
            color="#bbe773"
            gradientFrom="#bbe773"
            gradientTo="#9dd245"
            description="Latest execution"
          />
          <StatCard
            title="Chunks Created"
            value={timelineEntries && timelineEntries.length > 0 ? timelineEntries[0].chunks_created : 0}
            icon={<IconScissors size={24} />}
            color="#ddde65"
            gradientFrom="#ddde65"
            gradientTo="#bbe773"
            description="Latest execution"
          />
          <StatCard
            title="Total Executions"
            value={hasStatsData && timelineStats ? timelineStats.statistics.total_executions : 0}
            icon={<IconPlayerPlay size={24} />}
            color="#3bc57d"
            gradientFrom="#3bc57d"
            gradientTo="#45c9bb"
            description={hasStatsData && timelineStats && timelineStats.statistics.successful_executions > 0
              ? `${timelineStats.statistics.successful_executions} successful`
              : 'No executions yet'}
          />
        </SimpleGrid>


        {/* Configuration Cards */}
        <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="lg">
          {/* Vector Database Collection */}
          {vectordbCollection && (
            <InfoSectionCard
              title="Vector Database"
              icon={<IconDatabase size={20} />}
              color="#bbe773"
              gradientFrom="#bbe773"
              gradientTo="#9dd245"
            >
              <Group gap="md" style={{ flexWrap: 'wrap' }}>
                <InfoItem label="Collection Name" value={vectordbCollection.collection_name} />
                <InfoItem label="Vector Dimension" value={vectordbCollection.vector_dimension} />
                <InfoItem label="Embedding Provider" value={getProviderName(vectordbCollection.embedding_model_provider_id)} fullWidth />
                <InfoItem label="Embedding Model" value={vectordbCollection.embedding_model_name} fullWidth />
                {vectordbCollection.description && (
                  <InfoItem label="Description" value={vectordbCollection.description} fullWidth />
                )}
              </Group>
            </InfoSectionCard>
          )}

          {/* Document Splitting */}
          <InfoSectionCard
            title="Document Splitting"
            icon={<IconScissors size={20} />}
            color="#ddde65"
            gradientFrom="#ddde65"
            gradientTo="#bbe773"
          >
            <Group gap="md" style={{ flexWrap: 'wrap' }}>
              <InfoItem label="Splitter Type" value={job.document_splitter?.splitter_type || 'text'} />
              {(job.document_splitter?.splitter_type === 'text' || job.document_splitter?.splitter_type === 'document') && (
                <>
                  <InfoItem label="Chunk Size" value={`${job.document_splitter?.chunk_size || 256} tokens`} />
                  <InfoItem label="Chunk Overlap" value={`${job.document_splitter?.chunk_overlap || 32} tokens`} />
                </>
              )}
              {job.document_splitter?.splitter_type === 'document' && job.document_splitter?.headers_to_split_on && (
                <InfoItem
                  label="Headers to Split On"
                  value={job.document_splitter.headers_to_split_on.map(([pattern, name]) => `${pattern} (${name})`).join(', ')}
                  fullWidth
                />
              )}
            </Group>
          </InfoSectionCard>

          {/* Processing Settings */}
          <InfoSectionCard
            title="Processing Settings"
            icon={<IconCpu size={20} />}
            color="#3bc57d"
            gradientFrom="#3bc57d"
            gradientTo="#45c9bb"
          >
            <Group gap="md" style={{ flexWrap: 'wrap' }}>
              <InfoItem label="Batch Size" value={`${job.batch_size} documents`} />
              <InfoItem label="Save to File" value={job.save_to_file ? '✓ Yes' : '✗ No'} />
              <InfoItem label="Consolidated File" value={job.write_consolidated_file ? '✓ Yes' : '✗ No'} />
              <InfoItem label="Clear Collection" value={job.clear_collection_before_start ? '✓ Yes' : '✗ No'} />
              <InfoItem label="Check Duplicates" value={job.check_duplicates_before_insert ? '✓ Yes' : '✗ No'} />
            </Group>
          </InfoSectionCard>
        </SimpleGrid>

        {/* Job Information */}
        <InfoSectionCard
          title="Job Information"
          icon={<IconInfoCircle size={20} />}
          color="#ae89ae"
          gradientFrom="#ae89ae"
          gradientTo="#87cbbc"
        >
          <Group gap="md" style={{ flexWrap: 'wrap' }}>
            <InfoItem label="Job ID" value={<Code>{job.id}</Code>} />
            <InfoItem label="Collection ID" value={<Code>{job.vectordb_collection_id}</Code>} />
            <InfoItem
              label="Created"
              value={(() => {
                const date = new Date(job.created_at);
                return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
              })()}
            />
            <InfoItem label="Created By" value={job.created_by} />
            {timelineEntries && timelineEntries.length > 0 && timelineEntries[0] && (
              <>
                {timelineEntries[0].started_at && (
                  <InfoItem
                    label="Latest Started"
                    value={(() => {
                      const date = new Date(timelineEntries[0].started_at);
                      return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                    })()}
                  />
                )}
                {timelineEntries[0].completed_at && (
                  <InfoItem
                    label="Latest Completed"
                    value={(() => {
                      const date = new Date(timelineEntries[0].completed_at);
                      return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                    })()}
                  />
                )}
              </>
            )}
          </Group>
        </InfoSectionCard>

        {/* Timeline */}
        <InfoSectionCard
          title="Job Execution Timeline"
          icon={<IconClock size={20} />}
          color="#45c9bb"
          gradientFrom="#45c9bb"
          gradientTo="#87cbbc"
        >
          <Stack gap="md">
            {hasStatsData && timelineStats && (
              <Group gap="md">
                <Badge color="blue" variant="light" size="lg">
                  {timelineStats.statistics.total_executions} executions
                </Badge>
                <Badge color="green" variant="light" size="lg">
                  {timelineStats.statistics.successful_executions} successful
                </Badge>
                {timelineStats.statistics.failed_executions > 0 && (
                  <Badge color="red" variant="light" size="lg">
                    {timelineStats.statistics.failed_executions} failed
                  </Badge>
                )}
              </Group>
            )}

            {hasTimelineData && timelineItems.length > 0 ? (
              <Box style={{ maxHeight: '500px', overflowY: 'auto', paddingRight: '8px' }}>
                <Timeline active={timelineItems.length - 1}>
                  {timelineItems.map((item, index) => (
                    <Timeline.Item
                      key={item.entry.id}
                      bullet={<item.icon size={12} />}
                      title={item.title}
                      color={item.color}
                    >
                      <Stack gap="xs">
                        <Text size="sm" c="dimmed">
                          {item.description}
                        </Text>
                        <Group gap="md" style={{ flexWrap: 'wrap' }}>
                          <Text size="xs" c="dimmed">
                            Started: {item.entry.started_at ? (() => {
                              const date = new Date(item.entry.started_at);
                              return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                            })() : 'Not started'}
                          </Text>
                          {item.entry.completed_at && (
                            <Text size="xs" c="dimmed">
                              Completed: {(() => {
                                const date = new Date(item.entry.completed_at);
                                return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
                              })()}
                            </Text>
                          )}
                          {item.entry.processing_time_seconds > 0 && (
                            <Text size="xs" c="dimmed">
                              Duration: {item.entry.processing_time_seconds}s
                            </Text>
                          )}
                        </Group>
                        {item.entry.error_message && (
                          <Alert color="red" variant="light">
                            <Text size="xs">{item.entry.error_message}</Text>
                          </Alert>
                        )}
                      </Stack>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Box>
            ) : (
              <Alert color="blue" title="No Executions Yet" variant="light">
                <Text size="sm">This job hasn't been executed yet. Timeline entries will appear here after the job is run.</Text>
              </Alert>
            )}
          </Stack>
        </InfoSectionCard>

      </Stack>
    </Page>
  );
}
