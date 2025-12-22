import { ActionIcon, Alert, Badge, Box, Card, Group, Stack, Text, Tooltip } from '@mantine/core';
import { useClipboard } from '@mantine/hooks';
import { IconAlertTriangle, IconCheck, IconCopy, IconRobot, IconSparkles } from '@tabler/icons-react';
import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { detectTextDirection } from '../utilities/text-direction';
import { DocumentCard } from './document-card';
import { EnhancedCodeBlock } from './enhanced-code-block';
import { EnhancedMetadataSection } from './enhanced-metadata-section';

interface MessageMetadata {
  source_links?: Array<{
    url: string;
    title: string;
    chunk_id?: string;
    query_variant_index?: number;
    query_variant?: string;
  }>;  // Structured links with URL, title, chunk_id, and variant info
  document_count?: number;
  enhancement_strategy?: string;
  enhanced_query?: string;
  enhanced_queries?: string[];
}

interface EnhancedMessageRendererProps {
  content: string;
  metadata?: MessageMetadata;
  isRawMode?: boolean;
}

export function EnhancedMessageRenderer({
  content,
  metadata,
  isRawMode = false,
}: EnhancedMessageRendererProps) {
  const clipboard = useClipboard({ timeout: 2000 });

  // Detect text direction based on content
  const textDirection = useMemo(() => detectTextDirection(content || ''), [content]);

  // Memoize markdown components to prevent infinite re-renders
  const markdownComponents = useMemo(() => ({
    code({ inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const code = String(children).replace(/\n$/, '');
      return <EnhancedCodeBlock code={code} language={match ? match[1] : undefined} inline={inline} />;
    },
    h1: ({ children }: any) => (
      <Text size="20px" fw={700} mt="md" mb="xs" c="gray.9" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h2: ({ children }: any) => (
      <Text size="18px" fw={600} mt="md" mb="xs" c="gray.9" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h3: ({ children }: any) => (
      <Text size="16px" fw={600} mt="sm" mb="xs" c="gray.8" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    h4: ({ children }: any) => (
      <Text size="14px" fw={600} mt="sm" mb="xs" c="gray.8" style={{ lineHeight: 1.3 }}>
        {children}
      </Text>
    ),
    ul: ({ children }: any) => (
      <ul style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '24px' }}>
        {children}
      </ul>
    ),
    ol: ({ children }: any) => (
      <ol style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '24px' }}>
        {children}
      </ol>
    ),
    li: ({ children }: any) => (
      <li style={{ marginTop: '4px', marginBottom: '4px', lineHeight: '1.6' }}>
        {children}
      </li>
    ),
    p: ({ children }: any) => (
      <Text component="div" style={{ marginTop: '8px', marginBottom: '8px', lineHeight: '1.6' }}>
        {children}
      </Text>
    ),
    strong: ({ children }: any) => (
      <Text component="strong" fw={600} c="gray.9">
        {children}
      </Text>
    ),
    em: ({ children }: any) => (
      <Text component="em" fs="italic" c="gray.8">
        {children}
      </Text>
    ),
    a: ({ href, children }: any) => (
      <Text
        component="a"
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        c="blue.6"
        style={{
          textDecoration: 'underline',
        }}
      >
        {children}
      </Text>
    ),
    blockquote: ({ children }: any) => (
      <Box
        style={{
          borderLeft: '4px solid var(--mantine-color-indigo-5)',
          paddingLeft: '20px',
          paddingTop: '8px',
          paddingBottom: '8px',
          marginTop: '16px',
          marginBottom: '16px',
          backgroundColor: 'var(--mantine-color-indigo-0)',
          borderRadius: '0 4px 4px 0',
        }}
      >
        <Text c="gray.8" fs="italic">
          {children}
        </Text>
      </Box>
    ),
    hr: () => (
      <Box
        style={{
          height: '1px',
          backgroundColor: 'var(--mantine-color-gray-3)',
          margin: '24px 0',
          border: 'none',
        }}
      />
    ),
    table: ({ children }: any) => (
      <Box style={{ overflowX: 'auto', marginTop: '20px', marginBottom: '20px' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '14px',
            border: '1px solid var(--mantine-color-gray-3)',
          }}
        >
          {children}
        </table>
      </Box>
    ),
    thead: ({ children }: any) => (
      <thead style={{ backgroundColor: 'var(--mantine-color-gray-1)' }}>
        {children}
      </thead>
    ),
    tbody: ({ children }: any) => (
      <tbody>
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }: any) => {
      const isHeader = props.node?.parent?.tagName === 'thead';
      return (
        <tr
          style={{
            borderBottom: '1px solid var(--mantine-color-gray-3)',
            backgroundColor: !isHeader && props.node?.position?.start?.line % 2 === 0
              ? 'var(--mantine-color-gray-0)'
              : 'transparent',
          }}
        >
          {children}
        </tr>
      );
    },
    th: ({ children }: any) => (
      <th
        style={{
          padding: '12px 16px',
          textAlign: 'left',
          fontWeight: 600,
          borderBottom: '2px solid var(--mantine-color-gray-4)',
          color: 'var(--mantine-color-gray-9)',
        }}
      >
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td
        style={{
          padding: '12px 16px',
          color: 'var(--mantine-color-gray-8)',
        }}
      >
        {children}
      </td>
    ),
  }), []); // Empty deps - these components don't depend on any props or state

  // Prepare sources data - memoized to prevent infinite re-renders
  const sources = useMemo(() => {
    if (!metadata?.source_links || metadata.source_links.length === 0) {
      return [];
    }

    // Group by URL (since same URL might appear multiple times with different chunk_ids and variants)
    const urlGroups: { [url: string]: { title: string; chunkIds: string[]; queryVariants: Array<{ index: number; text: string }> } } = {};

    metadata.source_links.forEach((link) => {
      if (!urlGroups[link.url]) {
        urlGroups[link.url] = { title: link.title, chunkIds: [], queryVariants: [] };
      }
      if (link.chunk_id) {
        urlGroups[link.url].chunkIds.push(link.chunk_id);
      }
      // Track which variant retrieved this document
      if (link.query_variant_index && link.query_variant) {
        // Avoid duplicate variants
        const variantExists = urlGroups[link.url].queryVariants.some(v => v.index === link.query_variant_index);
        if (!variantExists) {
          urlGroups[link.url].queryVariants.push({
            index: link.query_variant_index,
            text: link.query_variant
          });
        }
      }
    });

    const result = Object.entries(urlGroups).map(([url, data]) => ({
      url,
      title: data.title,
      chunkIds: data.chunkIds || [],
      queryVariants: data.queryVariants.length > 0 ? data.queryVariants : undefined,
    }));

    return result;
  }, [metadata?.source_links]);

  // Check if this is raw results mode by examining content
  const isActualRawMode = isRawMode || (content?.includes('**Raw Results Mode**') || false);

  // Parse documents - memoized to prevent infinite re-renders
  const documents = useMemo(() => {
    if (!isActualRawMode || !content) {
      return [];
    }

    // Parse raw results content
    const lines = content.split('\n');
    const docs: Array<{ content: string; sourceUrl?: string; chunkId?: string }> = [];

    let currentDoc: string[] = [];
    let inDocument = false;

    for (const line of lines) {
      if (line.startsWith('### Document ')) {
        // Start of new document
        if (currentDoc.length > 0) {
          docs.push({ content: currentDoc.join('\n').trim() });
        }
        currentDoc = [];
        inDocument = true;
      } else if (line.trim() === '---' || line.trim() === '') {
        // Skip separators and empty lines at document boundaries
        if (inDocument && currentDoc.length === 0) {
          continue;
        }
      } else if (inDocument) {
        currentDoc.push(line);
      }
    }

    // Add last document
    if (currentDoc.length > 0) {
      docs.push({ content: currentDoc.join('\n').trim() });
    }

    // Add source URLs and chunk IDs to documents
    if (sources.length > 0 && docs.length > 0) {
      const docsPerSource = Math.ceil(docs.length / sources.length);
      docs.forEach((doc, index) => {
        const sourceIndex = Math.floor(index / docsPerSource);
        if (sourceIndex < sources.length) {
          doc.sourceUrl = sources[sourceIndex].url;
          doc.chunkId = sources[sourceIndex].chunkIds[index % sources[sourceIndex].chunkIds.length];
        }
      });
    }

    return docs;
  }, [isActualRawMode, content, sources]);

  if (isActualRawMode) {

    return (
      <Stack gap="xs">
        {/* Raw Results Mode Alert */}
        <Alert
          icon={<IconAlertTriangle size={14} />}
          title="RAW RESULTS"
          color="orange"
          variant="filled"
          p="xs"
          styles={{
            root: {
              backgroundColor: 'var(--mantine-color-orange-6)',
            },
            title: {
              fontSize: '12px',
            },
          }}
        >
          <Text size="xs" c="white">
            {documents.length} unprocessed document{documents.length !== 1 ? 's' : ''} from knowledge base
          </Text>
        </Alert>

        {/* Document Cards */}
        {documents.map((doc, index) => (
          <DocumentCard
            key={index}
            content={doc.content}
            index={index + 1}
            total={documents.length}
            sourceUrl={doc.sourceUrl}
            chunkId={doc.chunkId}
          />
        ))}

        {/* Metadata Section */}
        {metadata && (
          <EnhancedMetadataSection
            documentCount={metadata.document_count || documents.length}
            enhancementStrategy={metadata.enhancement_strategy}
            enhancedQueries={metadata.enhanced_queries}
            sources={sources}
            collapsedByDefault={false}
          />
        )}
      </Stack>
    );
  }

  // LLM-Generated Mode
  return (
    <Stack gap="xs">
      {/* AI Response Header */}
      <Card
        padding="xs"
        radius="sm"
        withBorder
        style={{
          background: 'linear-gradient(135deg, var(--mantine-color-indigo-0) 0%, var(--mantine-color-blue-0) 100%)',
          border: '1px solid var(--mantine-color-indigo-3)',
        }}
      >
        <Group justify="space-between">
          <Group gap="xs">
            <IconRobot size={14} color="var(--mantine-color-indigo-6)" />
            <Text size="xs" fw={600} c="indigo.9">
              AI RESPONSE
            </Text>
            {metadata?.document_count && (
              <Badge size="xs" variant="light" color="indigo">
                {metadata.document_count} {metadata.document_count === 1 ? 'source' : 'sources'}
              </Badge>
            )}
            {metadata?.enhancement_strategy && metadata.enhancement_strategy !== 'native' && (
              <Badge size="xs" variant="light" color="violet" leftSection={<IconSparkles size={10} />}>
                {metadata.enhancement_strategy}
              </Badge>
            )}
          </Group>
          <Tooltip label={clipboard.copied ? 'Copied!' : 'Copy response'}>
            <ActionIcon
              variant="subtle"
              color={clipboard.copied ? 'green' : 'indigo'}
              size="xs"
              onClick={() => clipboard.copy(content)}
            >
              {clipboard.copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
            </ActionIcon>
          </Tooltip>
        </Group>
      </Card>

      {/* Content */}
      <Card
        padding="sm"
        radius="sm"
        withBorder
        style={{
          backgroundColor: 'white',
          border: '1px solid var(--mantine-color-gray-2)',
        }}
      >
        <Box
          style={{
            fontSize: '14px',
            lineHeight: '1.6',
            color: 'var(--mantine-color-gray-9)',
            direction: textDirection,
            textAlign: textDirection === 'rtl' ? 'right' : 'left',
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {content || ''}
          </ReactMarkdown>
        </Box>
      </Card>

      {/* Metadata Section */}
      {metadata && (
        <EnhancedMetadataSection
          documentCount={metadata.document_count}
          enhancementStrategy={metadata.enhancement_strategy}
          enhancedQueries={metadata.enhanced_queries}
          sources={sources}
          collapsedByDefault={true}
        />
      )}
    </Stack>
  );
}
