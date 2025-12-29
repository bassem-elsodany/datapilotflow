/**
 * FilesGrid Component for Deep Agent
 *
 * Displays agent's file system in a grid layout.
 * Adapted from: https://github.com/langchain-ai/deep-agents-ui
 */

import type { FileContent, FileItem } from '@/types/deep-agent';
import { FileText, Download, FolderOpen } from 'lucide-react';
import { useState } from 'react';
import { Box, Grid, Card, Group, Stack, Text, ActionIcon, Tooltip, Container, Center } from '@mantine/core';
import { FileViewer } from './FileViewer';

interface FilesGridProps {
  files: Record<string, FileContent>;
  onSaveFile?: (path: string, content: string) => Promise<void>;
  editDisabled?: boolean;
}

export function FilesGrid({ files, onSaveFile, editDisabled = false }: FilesGridProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);

  const handleSaveFile = async (path: string, content: string) => {
    if (onSaveFile) {
      await onSaveFile(path, content);
    }
    setSelectedFile({ path, content });
  };

  const fileEntries = Object.entries(files);

  if (fileEntries.length === 0) {
    return (
      <Center style={{ height: '100%' }}>
        <Stack align="center" gap="md">
          <FolderOpen size={48} color="#d1d5db" />
          <Text size="lg" fw={500} c="dimmed">
            No files created yet. The agent will create files as needed.
          </Text>
        </Stack>
      </Center>
    );
  }

  return (
    <>
      <Container size="lg" py="xl">
        <Card shadow="sm" p="md" radius="md" withBorder mb="lg">
          <Group gap="md">
            <Box style={{ backgroundColor: '#dbeafe', padding: 8, borderRadius: 8 }}>
              <FolderOpen size={22} color="#1e40af" />
            </Box>
            <Stack gap={0}>
              <Text fw={700} size="lg">
                Files
              </Text>
              <Text size="sm" c="dimmed">
                {fileEntries.length} {fileEntries.length === 1 ? 'file' : 'files'}
              </Text>
            </Stack>
          </Group>
        </Card>

        <Stack gap="sm">
          {fileEntries.map(([path, content]) => {
            // Handle different content formats from Deep Agents
            let fileContent: string;
            let createdAt: string | null = null;
            let modifiedAt: string | null = null;

            // Check if content is an object with nested content property (Deep Agents with metadata)
            if (typeof content === 'object' && content !== null && 'content' in content) {
              const contentObj = content as { content: unknown; created_at?: string; modified_at?: string };
              const contentArray = contentObj.content;
              if (Array.isArray(contentArray)) {
                fileContent = contentArray.join('\n');
              } else {
                fileContent = String(contentArray || '');
              }
              // Extract metadata
              createdAt = contentObj.created_at || null;
              modifiedAt = contentObj.modified_at || null;
            }
            // Check if content is a direct array
            else if (Array.isArray(content)) {
              fileContent = content.join('\n');
            }
            // Fallback: treat as string
            else {
              fileContent = String(content || '');
            }

            const fileName = path.split('/').pop() || 'file.txt';
            const extension = fileName.split('.').pop()?.toLowerCase();

            // Format timestamps for display
            const formatTimestamp = (timestamp: string | null) => {
              if (!timestamp) return null;
              try {
                const date = new Date(timestamp);
                return date.toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                });
              } catch {
                return timestamp;
              }
            };

            let mimeType = 'text/plain';
            if (extension === 'html' || extension === 'htm') {
              mimeType = 'text/html';
            } else if (extension === 'json') {
              mimeType = 'application/json';
            } else if (extension === 'xml') {
              mimeType = 'application/xml';
            } else if (extension === 'md') {
              mimeType = 'text/markdown';
            }

            const handleDownload = () => {
              console.log('💾 [DOWNLOAD STARTED]', path);
              console.log('📊 [CONTENT LENGTH]', fileContent.length, 'characters');
              console.log('📊 [CONTENT FIRST 200 CHARS]', fileContent.substring(0, 200));
              console.log('📊 [CONTENT LAST 200 CHARS]', fileContent.substring(fileContent.length - 200));

              const blob = new Blob([fileContent], { type: mimeType });
              console.log('📊 [BLOB SIZE]', blob.size, 'bytes');

              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = fileName;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);

              console.log('✅ [DOWNLOAD COMPLETE]', fileName);
            };

            return (
              <Card key={path} shadow="sm" padding="md" radius="md" withBorder style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0f6ff';
                  e.currentTarget.style.borderColor = '#2563eb';
                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '';
                  e.currentTarget.style.borderColor = '';
                  e.currentTarget.style.boxShadow = '';
                }}
              >
                <Group justify="space-between" align="flex-start">
                  <Group gap="md" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                    <FileText size={28} color="#2563eb" style={{ flexShrink: 0 }} />
                    <Stack gap="xs" style={{ flex: 1, minWidth: 0 }}>
                      <div>
                        <Text fw={700} size="sm" c="var(--mantine-color-dark-9)">
                          {fileName}
                        </Text>
                        <Text size="xs" c="dimmed" style={{ wordBreak: 'break-all' }}>
                          {path}
                        </Text>
                      </div>
                      <Group gap="xs" align="center" wrap="wrap">
                        <Text size="xs" c="dimmed">
                          {fileContent.length.toLocaleString()} bytes
                        </Text>
                        <Text size="xs" c="dimmed">
                          {extension ? `• .${extension}` : '• no extension'}
                        </Text>
                      </Group>
                      {(createdAt || modifiedAt) && (
                        <Group gap="xs" align="center" wrap="wrap">
                          {createdAt && (
                            <Text size="xs" c="dimmed">
                              Created: {formatTimestamp(createdAt)}
                            </Text>
                          )}
                          {modifiedAt && (
                            <Text size="xs" c="dimmed">
                              Modified: {formatTimestamp(modifiedAt)}
                            </Text>
                          )}
                        </Group>
                      )}
                    </Stack>
                  </Group>
                  <Tooltip label="Download" withArrow position="left">
                    <ActionIcon variant="subtle" onClick={handleDownload}>
                      <Download size={18} color="#6b7280" />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Card>
            );
          })}
        </Stack>
      </Container>

      {selectedFile && (
        <FileViewer
          file={selectedFile}
          onSave={handleSaveFile}
          onClose={() => setSelectedFile(null)}
          editDisabled={editDisabled}
        />
      )}
    </>
  );
}

