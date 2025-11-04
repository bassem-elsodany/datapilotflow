/**
 * Job Settings Panel
 *
 * Allows users to configure job execution parameters before saving and executing the pipeline
 */

import { useForm } from '@mantine/form';
import {
  Modal,
  Stack,
  Text,
  TextInput,
  Textarea,
  NumberInput,
  Checkbox,
  Button,
  Group,
  Divider,
  Alert,
  Badge,
} from '@mantine/core';
import { IconCheck, IconAlertCircle, IconInfoCircle, IconSettings } from '@tabler/icons-react';

interface JobSettingsPanelProps {
  opened: boolean;
  onClose: () => void;
  onSave: (settings: JobSettings) => void;
  isLoading?: boolean;
  isEditing?: boolean;
}

export interface JobSettings {
  jobName: string;
  jobDescription?: string;
  batchSize: number;
  saveToFile: boolean;
  writeConsolidatedFile: boolean;
  clearCollectionBeforeStart: boolean;
  checkDuplicatesBeforeInsert: boolean;
}

export function JobSettingsPanel({ opened, onClose, onSave, isLoading = false, isEditing = false }: JobSettingsPanelProps) {
  const form = useForm({
    initialValues: {
      jobName: '',
      jobDescription: '',
      batchSize: 100,
      saveToFile: false,
      writeConsolidatedFile: false,
      clearCollectionBeforeStart: false,
      checkDuplicatesBeforeInsert: false,
    },

    validate: {
      jobName: (value) => {
        if (!value?.trim()) return 'Job name is required';
        if (value.length < 3) return 'Job name must be at least 3 characters';
        return null;
      },
      batchSize: (value) => {
        if (value < 1) return 'Batch size must be at least 1';
        if (value > 1000) return 'Batch size must not exceed 1000';
        return null;
      },
    },
  });

  const handleSave = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;

    onSave(form.values as JobSettings);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Job Configuration & Execution Settings"
      size="lg"
      padding="lg"
      centered
    >
      <Stack gap="lg">
        {/* Job Identity Section */}
        <div>
          <Group mb="md" gap="xs">
            <IconSettings size={18} color="#228be6" />
            <Text fw={600} size="sm">
              Job Identity
            </Text>
          </Group>

          <Stack gap="md">
            <TextInput
              label="Job Name"
              placeholder="e.g., Company Documentation Ingestion"
              description="A descriptive name for this knowledge processing job"
              required
              {...form.getInputProps('jobName')}
            />

            <Textarea
              label="Job Description (Optional)"
              placeholder="Describe what this job does, why it's needed, etc."
              rows={3}
              description="Additional context about this job"
              {...form.getInputProps('jobDescription')}
            />
          </Stack>
        </div>

        <Divider />

        {/* Processing Configuration Section */}
        <div>
          <Group mb="md" gap="xs">
            <IconInfoCircle size={18} color="#228be6" />
            <Text fw={600} size="sm">
              Processing Configuration
            </Text>
          </Group>

          <Stack gap="md">
            <NumberInput
              label="Batch Size"
              description="Number of documents to process in each batch (1-1000)"
              placeholder="100"
              min={1}
              max={1000}
              step={10}
              required
              {...form.getInputProps('batchSize')}
            />

            <Alert icon={<IconAlertCircle size={16} />} color="orange" variant="light">
              <Text size="xs">
                <strong>Batch Processing:</strong> Larger batches process faster but use more memory. Start with 100 and adjust based on your system resources.
              </Text>
            </Alert>
          </Stack>
        </div>

        <Divider />

        {/* File Output Options */}
        <div>
          <Group mb="md" gap="xs">
            <Text fw={600} size="sm">
              File Output Options
            </Text>
          </Group>

          <Stack gap="md">
            <Checkbox
              label="Save Extracted Content to Files"
              description="Write each extracted document to a separate file"
              {...form.getInputProps('saveToFile', { type: 'checkbox' })}
            />

            <Checkbox
              label="Write Consolidated File"
              description="Combine all content into a single file (memory intensive for large datasets)"
              disabled={!form.values.saveToFile}
              {...form.getInputProps('writeConsolidatedFile', { type: 'checkbox' })}
            />

            <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
              <Text size="xs">
                <strong>File Output:</strong> Extracted content is always stored in the vector database. These options save additional copies to disk.
              </Text>
            </Alert>
          </Stack>
        </div>

        <Divider />

        {/* Collection Management */}
        <div>
          <Group mb="md" gap="xs">
            <Text fw={600} size="sm">
              Collection Management
            </Text>
          </Group>

          <Stack gap="md">
            <Checkbox
              label="Clear Collection Before Start"
              description="Remove all existing data from the vector database collection before inserting new data"
              {...form.getInputProps('clearCollectionBeforeStart', { type: 'checkbox' })}
            />

            <Checkbox
              label="Check for Duplicates Before Insert"
              description="Prevent duplicate URLs/documents from being inserted into the collection"
              {...form.getInputProps('checkDuplicatesBeforeInsert', { type: 'checkbox' })}
            />

            <Alert icon={<IconAlertCircle size={16} />} color="red" variant="light">
              <Text size="xs">
                <strong>⚠️ Warning:</strong> Clearing the collection will permanently delete all existing data. Make sure you have backups if needed.
              </Text>
            </Alert>
          </Stack>
        </div>

        <Divider />

        {/* Execution Summary */}
        <div>
          <Text fw={600} size="sm" mb="md">
            Execution Summary
          </Text>

          <div style={{ backgroundColor: '#f8f9fa', padding: '12px', borderRadius: '6px' }}>
            <Stack gap="xs" size="xs">
              <Group justify="space-between">
                <Text size="sm">Job Name:</Text>
                <Badge size="lg" variant="light">
                  {form.values.jobName || '(not set)'}
                </Badge>
              </Group>

              <Group justify="space-between">
                <Text size="sm">Batch Size:</Text>
                <Badge size="lg" variant="light">
                  {form.values.batchSize} documents
                </Badge>
              </Group>

              {form.values.clearCollectionBeforeStart && (
                <Group justify="space-between">
                  <Text size="sm" c="red">
                    ⚠️ Collection will be cleared
                  </Text>
                  <Badge size="lg" color="red" variant="light">
                    Destructive
                  </Badge>
                </Group>
              )}

              {form.values.saveToFile && (
                <Group justify="space-between">
                  <Text size="sm">File Output:</Text>
                  <Badge size="lg" variant="light">
                    {form.values.writeConsolidatedFile ? 'Single consolidated file' : 'Multiple files'}
                  </Badge>
                </Group>
              )}
            </Stack>
          </div>
        </div>

        {/* Action Buttons */}
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            color="green"
            leftSection={<IconCheck size={16} />}
            onClick={handleSave}
            loading={isLoading}
          >
            {isEditing ? 'Update Job Configuration' : 'Save & Execute Job'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
