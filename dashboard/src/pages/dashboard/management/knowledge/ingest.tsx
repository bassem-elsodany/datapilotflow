import { client } from '@/api/axios';
import { Page } from '@/components/page';
import { PageHeader } from '@/components/page-header';
import { paths } from '@/routes/paths';
import {
  Alert,
  Badge,
  Button,
  Card,
  Code,
  FileInput,
  Grid,
  Group,
  Paper,
  Progress,
  Stack,
  Text,
  Textarea,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconRefresh, IconUpload, IconX } from '@tabler/icons-react';
import { useState } from 'react';

interface UploadResult {
  file_id: string;
  status: string;
  filename?: string;
  message?: string;
  processing_results?: any;
}

const breadcrumbs = [
  { label: 'Dashboard', href: paths.dashboard.root },
  { label: 'Management', href: paths.dashboard.management.root },
  { label: 'Knowledge', href: paths.dashboard.management.knowledge.root },
  { label: 'Ingest' },
];

export default function KnowledgeIngestPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const handleFileSelect = (file: File | null) => {
    if (file) {
      setSelectedFile(file);
      setUploadError('');
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus('🔄 Starting upload...');
    setUploadError('');
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (description) {
        formData.append('description', description);
      }

      const response = await client.post('/knowledge/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;
      setUploadResult(result);
      setJobId(result.file_id);
      setUploadStatus('✅ Upload completed successfully!');
      setUploadProgress(100);

      notifications.show({
        title: 'Upload Successful',
        message: 'File uploaded successfully. Processing started.',
        color: 'green',
        icon: <IconCheck size="1rem" />,
      });

      // Start polling for status
      pollJobStatus(result.file_id);
    } catch (error: any) {
      console.error('Upload failed:', error);
      setUploadError(error.response?.data?.detail || 'Upload failed');
      setUploadStatus('❌ Upload failed');

      notifications.show({
        title: 'Upload Failed',
        message: error.response?.data?.detail || 'Upload failed',
        color: 'red',
        icon: <IconX size="1rem" />,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await client.get(`/knowledge/status/${jobId}`);
        const status = response.data;

        // Update progress based on status
        const progressMap: Record<string, number> = {
          queued: 10,
          processing: 30,
          chunking: 50,
          enrichment: 70,
          embedding: 90,
          completed: 100,
        };

        setUploadProgress(progressMap[status.status] || 0);
        setUploadStatus(`🔄 ${status.status}: ${status.message || ''}`);

        if (status.status === 'completed') {
          setUploadStatus('✅ Processing completed!');
          setUploadResult(status);
          notifications.show({
            title: 'Processing Complete',
            message: 'File processing completed successfully.',
            color: 'green',
            icon: <IconCheck size="1rem" />,
          });
          return;
        } else if (status.status === 'error' || status.status === 'failed') {
          setUploadStatus('❌ Processing failed');
          setUploadError(status.message || 'Processing failed');
          notifications.show({
            title: 'Processing Failed',
            message: status.message || 'Processing failed',
            color: 'red',
            icon: <IconX size="1rem" />,
          });
          return;
        }

        // Continue polling
        setTimeout(poll, 2000);
      } catch (error) {
        console.error('Status polling failed:', error);
      }
    };

    poll();
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setDescription('');
    setUploadProgress(0);
    setUploadStatus('');
    setUploadResult(null);
    setUploadError('');
    setJobId(null);
  };

  return (
    <Page title="Knowledge Ingestion">
      <PageHeader title="Knowledge Ingestion" breadcrumbs={breadcrumbs} />

      <Grid>
        <Grid.Col span={12}>
          <Card withBorder>
            <Stack gap="lg">
              <Title order={3} size="h4">
                📤 Upload Knowledge File
              </Title>

              {/* File Upload */}
              <FileInput
                label="Select File"
                placeholder="Choose a file to upload"
                accept=".pdf,.docx,.txt,.md,.html,.xml"
                value={selectedFile}
                onChange={handleFileSelect}
                disabled={isUploading}
                description="Supported formats: PDF, DOCX, TXT, MD, HTML, XML"
              />

              {/* Description */}
              <Textarea
                label="Description (Optional)"
                placeholder="Enter a description for this file..."
                value={description}
                onChange={(event) => setDescription(event.currentTarget.value)}
                disabled={isUploading}
                minRows={3}
              />

              {/* Upload Actions */}
              <Group>
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                  loading={isUploading}
                  leftSection={<IconUpload size="1rem" />}
                  size="md"
                >
                  {isUploading ? 'Uploading...' : 'Upload & Process'}
                </Button>

                {uploadResult && (
                  <Button
                    onClick={resetUpload}
                    variant="outline"
                    leftSection={<IconRefresh size="1rem" />}
                    size="md"
                  >
                    Upload Another File
                  </Button>
                )}
              </Group>
            </Stack>
          </Card>
        </Grid.Col>

        {/* Progress Section */}
        {isUploading && (
          <Grid.Col span={12}>
            <Card withBorder>
              <Stack gap="md">
                <Title order={4} size="h5">
                  Upload Progress
                </Title>
                <Progress
                  value={uploadProgress}
                  size="lg"
                  radius="md"
                  color="blue"
                  striped
                  animated
                />
                <Text size="sm" c="dimmed">
                  {uploadProgress}% - {uploadStatus}
                </Text>
              </Stack>
            </Card>
          </Grid.Col>
        )}

        {/* Error Section */}
        {uploadError && (
          <Grid.Col span={12}>
            <Alert
              icon={<IconX size="1rem" />}
              title="Upload Error"
              color="red"
              variant="light"
            >
              {uploadError}
            </Alert>
          </Grid.Col>
        )}

        {/* Results Section */}
        {uploadResult && (
          <Grid.Col span={12}>
            <Card withBorder>
              <Stack gap="lg">
                <Group>
                  <IconCheck size="1.5rem" color="green" />
                  <Title order={4} size="h5" c="green">
                    Upload Results
                  </Title>
                </Group>

                <Paper withBorder p="md">
                  <Stack gap="xs">
                    <Group>
                      <Text fw={500}>File ID:</Text>
                      <Badge variant="light">{uploadResult.file_id}</Badge>
                    </Group>
                    <Group>
                      <Text fw={500}>Status:</Text>
                      <Badge
                        color={uploadResult.status === 'completed' ? 'green' : 'blue'}
                        variant="light"
                      >
                        {uploadResult.status}
                      </Badge>
                    </Group>
                    {uploadResult.filename && (
                      <Group>
                        <Text fw={500}>Filename:</Text>
                        <Text>{uploadResult.filename}</Text>
                      </Group>
                    )}
                    {uploadResult.message && (
                      <Group>
                        <Text fw={500}>Message:</Text>
                        <Text>{uploadResult.message}</Text>
                      </Group>
                    )}
                  </Stack>
                </Paper>

                {uploadResult.processing_results && (
                  <Paper withBorder p="md">
                    <Title order={5} size="h6" mb="md">
                      📊 Processing Results
                    </Title>
                    <Code block>
                      {JSON.stringify(uploadResult.processing_results, null, 2)}
                    </Code>
                  </Paper>
                )}
              </Stack>
            </Card>
          </Grid.Col>
        )}
      </Grid>
    </Page>
  );
}
