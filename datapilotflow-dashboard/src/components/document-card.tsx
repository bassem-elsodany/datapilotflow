import { ActionIcon, Anchor, Badge, Box, Card, Divider, Group, Stack, Text, Tooltip } from '@mantine/core';
import { useClipboard } from '@mantine/hooks';
import { IconCheck, IconCopy, IconExternalLink, IconFileText, IconHash } from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { EnhancedCodeBlock } from './enhanced-code-block';

interface DocumentCardProps {
  content: string;
  index: number;
  total: number;
  sourceUrl?: string;
  chunkId?: string;
}

export function DocumentCard({
  content,
  index,
  total,
  sourceUrl,
  chunkId,
}: DocumentCardProps) {
  const clipboard = useClipboard({ timeout: 2000 });

  return (
    <Card
      shadow="sm"
      padding="sm"
      radius="sm"
      withBorder
      style={{
        borderColor: 'var(--mantine-color-orange-3)',
        backgroundColor: 'var(--mantine-color-orange-0)',
        marginBottom: '8px',
      }}
    >
      {/* Header */}
      <Group justify="space-between" mb="xs">
        <Group gap="xs">
          <IconFileText size={14} color="var(--mantine-color-orange-7)" />
          <Text size="xs" fw={600} c="orange.9">
            Document {index} of {total}
          </Text>
        </Group>
        <Group gap="xs">
          {sourceUrl && (
            <Tooltip label="Open source">
              <ActionIcon
                variant="light"
                color="orange"
                size="sm"
                component="a"
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                <IconExternalLink size={14} />
              </ActionIcon>
            </Tooltip>
          )}
          <Tooltip label={clipboard.copied ? 'Copied!' : 'Copy content'}>
            <ActionIcon
              variant="light"
              color={clipboard.copied ? 'green' : 'orange'}
              size="sm"
              onClick={() => clipboard.copy(content)}
            >
              {clipboard.copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Divider mb="xs" color="orange.3" />

      {/* Content */}
      <Box
        style={{
          fontSize: '13px',
          lineHeight: '1.6',
          color: 'var(--mantine-color-gray-9)',
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const code = String(children).replace(/\n$/, '');
              return <EnhancedCodeBlock code={code} language={match ? match[1] : undefined} inline={inline} />;
            },
            h1: ({ children }) => (
              <Text size="lg" fw={700} mt="sm" mb="xs" c="orange.9">
                {children}
              </Text>
            ),
            h2: ({ children }) => (
              <Text size="md" fw={600} mt="sm" mb="xs" c="orange.8">
                {children}
              </Text>
            ),
            h3: ({ children }) => (
              <Text size="sm" fw={600} mt="xs" mb="xs" c="orange.7">
                {children}
              </Text>
            ),
            ul: ({ children }) => (
              <ul style={{ marginTop: '6px', marginBottom: '6px', paddingLeft: '20px' }}>
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol style={{ marginTop: '6px', marginBottom: '6px', paddingLeft: '20px' }}>
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li style={{ marginTop: '3px', marginBottom: '3px', lineHeight: '1.5' }}>
                {children}
              </li>
            ),
            p: ({ children }) => (
              <Text component="p" style={{ marginTop: '6px', marginBottom: '6px', lineHeight: '1.6' }}>
                {children}
              </Text>
            ),
            strong: ({ children }) => (
              <Text component="strong" fw={600} c="gray.9">
                {children}
              </Text>
            ),
            a: ({ href, children }) => (
              <Anchor
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                c="blue.6"
                style={{
                  textDecoration: 'none',
                  borderBottom: '1px solid var(--mantine-color-blue-3)',
                }}
              >
                {children}
              </Anchor>
            ),
            blockquote: ({ children }) => (
              <Box
                style={{
                  borderLeft: '3px solid var(--mantine-color-orange-5)',
                  paddingLeft: '12px',
                  marginTop: '6px',
                  marginBottom: '6px',
                  color: 'var(--mantine-color-gray-7)',
                  fontStyle: 'italic',
                }}
              >
                {children}
              </Box>
            ),
            table: ({ children }) => (
              <Box style={{ overflowX: 'auto', marginTop: '8px', marginBottom: '8px' }}>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '12px',
                  }}
                >
                  {children}
                </table>
              </Box>
            ),
            thead: ({ children }) => (
              <thead style={{ backgroundColor: 'var(--mantine-color-gray-1)' }}>
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody>
                {children}
              </tbody>
            ),
            tr: ({ children }) => (
              <tr
                style={{
                  borderBottom: '1px solid var(--mantine-color-gray-3)',
                }}
              >
                {children}
              </tr>
            ),
            th: ({ children }) => (
              <th
                style={{
                  padding: '8px',
                  textAlign: 'left',
                  fontWeight: 600,
                  borderBottom: '2px solid var(--mantine-color-gray-4)',
                }}
              >
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td
                style={{
                  padding: '8px',
                }}
              >
                {children}
              </td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </Box>

      {/* Footer with source info */}
      {(sourceUrl || chunkId) && (
        <>
          <Divider mt="xs" mb="xs" color="orange.3" />
          <Stack gap={4}>
            {sourceUrl && (
              <Group gap="xs" wrap="nowrap">
                <IconExternalLink size={14} color="var(--mantine-color-orange-6)" style={{ flexShrink: 0 }} />
                <Anchor
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  size="xs"
                  c="orange.7"
                  style={{ wordBreak: 'break-all' }}
                >
                  {sourceUrl}
                </Anchor>
              </Group>
            )}
            {chunkId && (
              <Group gap="xs">
                <IconHash size={14} color="var(--mantine-color-orange-6)" />
                <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>
                  {chunkId}
                </Text>
              </Group>
            )}
          </Stack>
        </>
      )}
    </Card>
  );
}
