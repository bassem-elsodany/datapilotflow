/**
 * Job Actions Component
 * 
 * This component provides action buttons for a job based on its timeline status.
 */

import { useLatestJobTimelineEntry } from '@/api/resources/job-timelines';
import { KnowledgeJob, useCancelKnowledgeJob } from '@/api/resources/knowledge-jobs';
import { paths } from '@/routes/paths';
import { ActionIcon, Alert, Button, Group, Modal, Stack, Text, Tooltip } from '@mantine/core';
import {
  IconAlertTriangle,
  IconEdit,
  IconEye,
  IconMessagePlus,
  IconPlayerPlay,
  IconPlayerStop,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface JobActionsProps {
  job: KnowledgeJob;
  onExecute?: (jobId: string) => void;
  onDelete?: (jobId: string, jobName: string) => void;
  onCancel?: (jobId: string) => void;
  onViewDetails?: (job: KnowledgeJob) => void;
  isExecuting?: boolean;
  isDeleting?: boolean;
}

export function JobActions({
  job,
  onExecute,
  onDelete,
  onCancel,
  onViewDetails,
  isExecuting = false,
  isDeleting = false
}: JobActionsProps) {
  const navigate = useNavigate();
  const { data: timelineEntries } = useLatestJobTimelineEntry(job.id);
  const cancelJobMutation = useCancelKnowledgeJob();
  const [clearCollectionModalOpen, setClearCollectionModalOpen] = useState(false);

  // Get the first (latest) timeline entry from the array
  const latestTimeline = timelineEntries && timelineEntries.length > 0 ? timelineEntries[0] : null;

  // Helper function to determine if a job can be executed (started/re-run)
  const canExecuteJob = () => {
    if (!latestTimeline) {
      return true; // Never executed, can execute
    }

    // Can execute if latest execution is created, completed, failed, or cancelled
    return ['created', 'completed', 'failed', 'cancelled'].includes(latestTimeline.status);
  };

  // Helper function to determine if a job is currently running or pending
  const isJobRunning = () => {
    return latestTimeline?.status === 'running' || latestTimeline?.status === 'pending';
  };

  // Helper function to determine if a job failed and can be retried
  const canRetryJob = () => {
    return latestTimeline?.status === 'failed';
  };


  const canExecute = canExecuteJob();
  const isRunning = isJobRunning();
  const canRetry = canRetryJob();

  // Debug logging
  console.log(`JobActions for ${job.id}:`, {
    timelineEntries,
    latestTimeline,
    status: latestTimeline?.status,
    canExecute,
    canRetry,
    shouldShowExecute: canExecute && !canRetry,
    isRunning
  });

  // Handler for execute/retry actions
  const handleExecuteClick = () => {
    // Check if job has "clear_collection_before_start" flag enabled
    if (job.clear_collection_before_start) {
      // Show confirmation modal
      setClearCollectionModalOpen(true);
    } else {
      // Execute directly
      onExecute?.(job.id);
    }
  };

  // Handler for confirming execution with collection clearing
  const handleConfirmExecution = () => {
    setClearCollectionModalOpen(false);
    onExecute?.(job.id);
  };

  return (
    <>
      {/* Clear Collection Confirmation Modal */}
      <Modal
        opened={clearCollectionModalOpen}
        onClose={() => setClearCollectionModalOpen(false)}
        title={
          <Group gap="sm">
            <IconAlertTriangle size={20} color="var(--mantine-color-orange-6)" />
            <Text fw={600} size="lg">Clear Collection Warning</Text>
          </Group>
        }
        centered
        size="md"
        radius="md"
        shadow="xl"
        styles={{
          header: {
            backgroundColor: 'var(--mantine-color-orange-0)',
            borderBottom: '1px solid var(--mantine-color-orange-2)',
            paddingBottom: '16px',
            marginBottom: '16px',
          },
        }}
      >
        <Stack gap="md">
          <Alert
            icon={<IconAlertTriangle size={16} />}
            title="Collection Will Be Cleared"
            color="orange"
            variant="light"
          >
            <Text>
              This job has <strong>"Clear Collection Data Before Starting"</strong> enabled.
            </Text>
          </Alert>

          <Text size="sm" c="dimmed">
            All existing data in the vector collection will be permanently deleted before this job starts processing.
            This action cannot be undone.
          </Text>

          <Text size="sm" fw={500}>
            Are you sure you want to continue?
          </Text>

          <Group justify="flex-end" gap="sm">
            <Button
              variant="light"
              onClick={() => setClearCollectionModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              color="orange"
              onClick={handleConfirmExecution}
              loading={isExecuting}
            >
              Yes, Clear and Start
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Action Buttons */}
      <Group gap={4} wrap="nowrap" justify="flex-end">
        {/* Always visible - View Details */}
        <Tooltip label="View Details">
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => onViewDetails ? onViewDetails(job) : navigate(`/dashboard/management/knowledge-sources/job-details/${job.id}`)}
          >
            <IconEye size={16} />
          </ActionIcon>
        </Tooltip>

        {/* Always visible - Edit Job */}
        <Tooltip label="Edit Job">
          <ActionIcon
            variant="subtle"
            color="orange"
            onClick={() => navigate(paths.dashboard.management.knowledgeSources.jobEdit(job.id))}
          >
            <IconEdit size={16} />
          </ActionIcon>
        </Tooltip>

        {/* Always visible - Create Conversation */}
        <Tooltip label="Create Conversation Agent">
          <ActionIcon
            variant="subtle"
            color="violet"
            onClick={() => navigate(paths.dashboard.apps.conversationCreate, {
              state: {
                fromJob: true,
                jobId: job.id,
                jobName: job.name,
                jobDescription: job.description,
                vectordbCollectionId: job.vectordb_collection_id
              }
            })}
          >
            <IconMessagePlus size={16} />
          </ActionIcon>
        </Tooltip>

        {/* Execute/Re-run button - show when job can be executed (but not failed) */}
        {canExecute && !canRetry && (
          <Tooltip label={latestTimeline ? "Re-run Job" : "Start Processing"}>
            <ActionIcon
              variant="subtle"
              color="blue"
              onClick={handleExecuteClick}
              loading={isExecuting}
              disabled={!onExecute}
            >
              <IconPlayerPlay size={16} />
            </ActionIcon>
          </Tooltip>
        )}

        {/* Cancel button - show when job is running or pending */}
        {isRunning && (
          <Tooltip label="Cancel Job">
            <ActionIcon
              variant="subtle"
              color="orange"
              onClick={() => {
                cancelJobMutation.mutate({
                  variables: {} as any,
                  route: { jobId: job.id }
                }, {
                  onSuccess: () => {
                    console.log('Job cancelled successfully');
                    onCancel?.(job.id);
                  },
                  onError: (error) => {
                    console.error('Failed to cancel job:', error);
                  }
                });
              }}
              loading={cancelJobMutation.isPending}
            >
              <IconPlayerStop size={16} />
            </ActionIcon>
          </Tooltip>
        )}

        {/* Retry button - show when job failed */}
        {canRetry && (
          <Tooltip label="Retry Job">
            <ActionIcon
              variant="subtle"
              color="green"
              onClick={handleExecuteClick}
              loading={isExecuting}
              disabled={!onExecute}
            >
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
        )}

        {/* Always visible - Delete */}
        <Tooltip label={isDeleting ? 'Deleting...' : 'Delete Job'}>
          <ActionIcon
            variant="subtle"
            color="red"
            onClick={() => onDelete?.(job.id, job.name)}
            disabled={isDeleting || !onDelete}
          >
            <IconTrash size={16} />
          </ActionIcon>
        </Tooltip>
      </Group>
    </>
  );
}
